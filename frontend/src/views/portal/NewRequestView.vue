<script setup lang="ts">
import { ArrowLeftRight, ClipboardList, ScanLine } from '@lucide/vue'
import { NButton, NSkeleton, useMessage } from 'naive-ui'
import { watchDebounced } from '@vueuse/core'
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { assetsApi } from '@/api/inventory'
import { portalApi, reservationsApi } from '@/api/reservations'
import PageHeader from '@/components/common/PageHeader.vue'
import CatalogBrowser from '@/components/reservations/request/CatalogBrowser.vue'
import ConsumableQuickPick from '@/components/reservations/request/ConsumableQuickPick.vue'
import DirectPicker from '@/components/reservations/request/DirectPicker.vue'
import RequestCart from '@/components/reservations/request/RequestCart.vue'
import RequestPeriodCard from '@/components/reservations/request/RequestPeriodCard.vue'
import {
  optionKey,
  periodQuery,
  type CartLine,
  type RequestPeriod,
} from '@/components/reservations/request/types'
import { useAction } from '@/composables/useAction'
import { useAuthStore } from '@/stores/auth'
import { anyModelLabel } from '@/utils/reservations'
import { useFeaturesStore } from '@/stores/features'
import type { Asset, Consumable } from '@/types/inventory'
import type {
  CatalogCategory,
  CatalogModel,
  DirectRequestInput,
  MyConsumables,
  ReservationInput,
} from '@/types/reservations'

const { t } = useI18n()
const features = useFeaturesStore()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const message = useMessage()
const { busy, run } = useAction()

/**
 * IT staff first choose between a request and a direct hand-out of specific
 * devices from stock (`?mode=direct`); everyone else only requests.
 */
const canDirect = computed(() => auth.can('reservations', 'write'))
const mode = computed<'request' | 'direct' | null>(() => {
  if (!canDirect.value) return 'request'
  const value = route.query.mode
  return value === 'direct' || value === 'request' ? value : null
})
const direct = computed(() => mode.value === 'direct')

function choose(value: 'request' | 'direct' | null) {
  router.replace({ query: value ? { mode: value } : {} })
}

const catalog = ref<CatalogCategory[] | null>(null)
const cart = ref<CartLine[]>([])
const myConsumables = ref<MyConsumables[]>([])

const today = new Date().setHours(0, 0, 0, 0)
const period = reactive<RequestPeriod>({
  duration: 'temporary',
  // Suggested period from the site settings (default loan period, start day included).
  range: [today, today + (features.rules.default_loan_days - 1) * 86400000],
  start: today,
  pickup: today,
})

// The two modes fill the cart differently; switching starts over.
watch(direct, () => (cart.value = []))

onMounted(async () => {
  // The quick pick can be switched off; its endpoint is gone then.
  const [entries, consumables] = await Promise.all([
    portalApi.catalog(periodQuery(period)),
    features.isOn('consumable_quick_pick') ? portalApi.myConsumables() : Promise.resolve([]),
  ])
  catalog.value = entries
  myConsumables.value = consumables
})

// From the device page: start the hand-out with that device.
watch(
  () => (direct.value ? route.query.asset : null),
  async (id) => {
    if (typeof id !== 'string') return
    const asset = await run(() => assetsApi.get(id))
    if (asset) addAsset(asset)
  },
  { immediate: true },
)

/** Lookup of what is free in the period, by cart/option key. */
function availableFor(key: string): number | null {
  for (const category of catalog.value ?? []) {
    if (key === optionKey(category)) return category.available
    const model = category.models.find((m) => key === optionKey(category, m))
    if (model) return model.available
  }
  return null
}

// IT handling requests sees availability for the chosen period: refresh the counts when it changes.
let latestQuery = 0
watchDebounced(
  () => periodQuery(period),
  async (query) => {
    if (!auth.can('reservations') || !catalog.value || direct.value) return
    const current = ++latestQuery
    const counts = await portalApi.availability(query)
    if (current !== latestQuery) return // a newer period was chosen meanwhile
    for (const category of catalog.value) {
      Object.assign(category, counts.categories[category.id] ?? { available: 0, reserved: 0 })
      for (const model of category.models) {
        Object.assign(model, counts.models[model.id] ?? { available: 0, reserved: 0 })
      }
    }
    for (const line of cart.value) line.available = availableFor(line.key)
  },
  { debounce: 250 },
)

const cartCounts = computed(() =>
  Object.fromEntries(cart.value.map((line) => [line.key, line.quantity])),
)

function add(category: CatalogCategory, model?: CatalogModel) {
  const key = optionKey(category, model)
  const existing = cart.value.find((line) => line.key === key)
  if (existing) {
    existing.quantity += 1
    return
  }
  cart.value.push({
    key,
    label: model ? model.full_name : anyModelLabel(category),
    category: model ? undefined : category.id,
    asset_model: model?.id,
    quantity: 1,
    note: '',
    available: model ? model.available : category.available,
  })
}

function addAsset(asset: Asset) {
  const key = `a${asset.id}`
  if (cart.value.some((line) => line.key === key)) return
  cart.value.push({
    key,
    label: asset.model.full_name,
    code: asset.inventory_number,
    asset: asset.id,
    quantity: 1,
    note: '',
    available: null,
  })
}

function addConsumable(consumable: Consumable) {
  const key = `s${consumable.id}`
  const existing = cart.value.find((line) => line.key === key)
  if (existing) {
    existing.quantity = Math.min(existing.quantity + 1, consumable.available_quantity)
    return
  }
  cart.value.push({
    key,
    label: consumable.model.full_name,
    consumable: consumable.id,
    quantity: 1,
    max: consumable.available_quantity,
    note: '',
    available: null,
  })
}

let freeTextCounter = 0

function addFreeText(text: string, category?: CatalogCategory) {
  cart.value.push({
    key: `f${++freeTextCounter}`,
    label: category ? `${category.name}: ${text}` : text,
    category: category?.id,
    description: text,
    quantity: 1,
    note: '',
    available: null,
  })
}

/** In a direct hand-out the cart holds devices and stocks instead of catalog lines. */
function directInput(data: ReservationInput): DirectRequestInput {
  const { items, ...fields } = data
  void items
  return {
    ...fields,
    assets: cart.value.flatMap((line) => (line.asset ? [line.asset] : [])),
    consumables: cart.value.flatMap((line) =>
      line.consumable ? [{ consumable: line.consumable, quantity: line.quantity }] : [],
    ),
  }
}

async function submit(data: ReservationInput) {
  const reservation = await run(() =>
    direct.value ? reservationsApi.createDirect(directInput(data)) : reservationsApi.create(data),
  )
  if (!reservation) return
  // IT continues on the request itself; employees follow it in the portal.
  if (auth.can('reservations')) {
    message.success(t('reservations.new.submitted', { number: reservation.number }))
    router.push({ name: 'reservation', params: { id: reservation.id } })
  } else {
    router.push({ name: 'portal-request', params: { id: reservation.id }, query: { created: '1' } })
  }
}

const header = computed(() =>
  direct.value
    ? { title: t('reservations.direct.title'), subtitle: t('reservations.direct.subtitle') }
    : { title: t('reservations.new.title'), subtitle: t('reservations.new.subtitle') },
)
</script>

<template>
  <div class="page">
    <template v-if="mode === null">
      <PageHeader
        :title="t('reservations.new.title')"
        :subtitle="t('reservations.direct.choose')"
      />
      <div class="choices">
        <button type="button" class="choice" @click="choose('request')">
          <ClipboardList :size="34" :stroke-width="1.3" />
          <strong>{{ t('reservations.direct.chooseRequest') }}</strong>
          <span class="muted">{{ t('reservations.direct.chooseRequestHint') }}</span>
        </button>
        <button type="button" class="choice" @click="choose('direct')">
          <ScanLine :size="34" :stroke-width="1.3" />
          <strong>{{ t('reservations.direct.title') }}</strong>
          <span class="muted">{{ t('reservations.direct.chooseDirectHint') }}</span>
        </button>
      </div>
    </template>

    <template v-else>
      <PageHeader :title="header.title" :subtitle="header.subtitle">
        <template v-if="canDirect" #actions>
          <NButton quaternary @click="choose(null)">
            <template #icon><ArrowLeftRight :size="15" /></template>
            {{ t('reservations.direct.switch') }}
          </NButton>
        </template>
      </PageHeader>
      <div class="layout">
        <NSkeleton v-if="!catalog" height="320px" />
        <CatalogBrowser
          v-else
          :catalog="catalog"
          :cart-counts="cartCounts"
          :direct="direct"
          @add="add"
          @add-free-text="addFreeText"
        >
          <ConsumableQuickPick
            :groups="myConsumables"
            :catalog="catalog"
            :cart-counts="cartCounts"
            @add="add"
          />
          <template #direct="{ category }">
            <DirectPicker
              :category="category"
              :cart-counts="cartCounts"
              @add-asset="addAsset"
              @add-consumable="addConsumable"
            />
          </template>
        </CatalogBrowser>
        <div class="side">
          <RequestPeriodCard v-model="period" :shows-availability="auth.can('reservations')" />
          <RequestCart
            :key="mode"
            v-model:lines="cart"
            :period="period"
            :busy="busy"
            :direct="direct"
            :can-choose-requester="canDirect"
            :requester-placeholder="auth.user?.display_name"
            @submit="submit"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.side {
  position: sticky;
  top: 16px;
  display: grid;
  gap: 14px;
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) clamp(340px, 28%, 440px);
  gap: 14px;
  align-items: start;
}
.choices {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 360px));
  gap: 16px;
}
.choice {
  display: grid;
  justify-items: start;
  gap: 10px;
  padding: 28px 26px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  color: var(--ar-text-muted);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}
.choice:hover,
.choice:focus-visible {
  border-color: var(--ar-primary);
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
.choice strong {
  color: var(--ar-text);
  font-size: 16px;
  font-weight: 600;
}
.choice .muted {
  line-height: 1.5;
}
@media (max-width: 1080px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .side {
    position: static;
  }
}
@media (max-width: 760px) {
  .choices {
    grid-template-columns: 1fr;
  }
}
</style>
