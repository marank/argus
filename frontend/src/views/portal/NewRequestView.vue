<script setup lang="ts">
import { ArrowLeftRight, ArrowRight, Check, ClipboardList, ScanLine } from '@lucide/vue'
import { NAlert, NButton, NSkeleton, useMessage } from 'naive-ui'
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
import { fromIsoDate } from '@/composables/useFormat'
import { useAuthStore } from '@/stores/auth'
import { anyModelLabel, itemLabel } from '@/utils/reservations'
import { useFeaturesStore } from '@/stores/features'
import type { UserRef } from '@/types/accounts'
import type { Asset, Consumable } from '@/types/inventory'
import type {
  CatalogCategory,
  CatalogModel,
  DirectRequestInput,
  MyConsumables,
  Reservation,
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
 * `?from=<id>` asks again for an earlier request: a request, prefilled.
 */
const canDirect = computed(() => auth.can('reservations', 'write'))
const mode = computed<'request' | 'direct' | null>(() => {
  if (!canDirect.value || route.query.from) return 'request'
  const value = route.query.mode
  return value === 'direct' || value === 'request' ? value : null
})
const direct = computed(() => mode.value === 'direct')

const choices = computed(() => [
  {
    mode: 'request' as const,
    icon: ClipboardList,
    title: t('reservations.direct.chooseRequest'),
    hint: t('reservations.direct.chooseRequestHint'),
    points: [
      t('reservations.direct.requestPoints.catalog'),
      t('reservations.direct.requestPoints.approval'),
      t('reservations.direct.requestPoints.confirm'),
    ],
  },
  {
    mode: 'direct' as const,
    icon: ScanLine,
    title: t('reservations.direct.title'),
    hint: t('reservations.direct.chooseDirectHint'),
    points: [
      t('reservations.direct.directPoints.scan'),
      t('reservations.direct.directPoints.noApproval'),
      t('reservations.direct.directPoints.protocol'),
    ],
  },
])

function choose(value: 'request' | 'direct' | null) {
  // A device from the device page stays picked whichever way is chosen.
  const asset = route.query.asset ? { asset: route.query.asset } : {}
  router.replace({ query: value ? { mode: value, ...asset } : asset })
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
  if (typeof route.query.from === 'string') {
    const earlier = await run(() => reservationsApi.get(route.query.from as string))
    if (earlier) prefill(earlier)
  }
})

/** Asking again: the earlier request's lines, details and period (moved to today if past). */
const previous = ref<Reservation | null>(null)
const initial = ref<{ title: string; notes: string; requester: UserRef | null } | null>(null)

function prefill(earlier: Reservation) {
  previous.value = earlier
  let freeText = 0
  cart.value = earlier.items.map((item) => {
    const key = item.description
      ? `f${++freeText}`
      : item.asset_model
        ? `m${item.asset_model.id}`
        : `c${item.category!.id}`
    return {
      key,
      label: itemLabel(item),
      category: item.asset_model ? undefined : item.category?.id,
      asset_model: item.asset_model?.id,
      description: item.description || undefined,
      quantity: item.quantity_requested,
      note: item.note,
      available: availableFor(key),
    }
  })
  const start = fromIsoDate(earlier.start_date)!
  const end = fromIsoDate(earlier.end_date) ?? start
  const first = Math.max(start, today)
  period.duration = earlier.duration
  period.start = first
  period.range = [first, first + Math.max(end - start, 0)]
  period.pickup = first
  initial.value = {
    title: earlier.title,
    notes: earlier.notes,
    // Recorded for someone else: keep them as the requester.
    requester: earlier.requester.id === auth.user?.id ? null : earlier.requester,
  }
}

// From the device page: hand out that device, or request its model.
watch(
  () => [mode.value, route.query.asset, catalog.value] as const,
  async ([current, id, entries]) => {
    if (typeof id !== 'string' || !current || (current === 'request' && !entries)) return
    const asset = await run(() => assetsApi.get(id))
    if (!asset) return
    if (current === 'direct') addAsset(asset)
    else addModelOf(asset)
  },
  { immediate: true },
)

function addModelOf(asset: Asset) {
  for (const category of catalog.value ?? []) {
    const model = category.models.find((m) => m.id === asset.model.id)
    if (!model) continue
    if (!cart.value.some((line) => line.key === optionKey(category, model))) add(category, model)
    return
  }
}

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
    direct.value
      ? reservationsApi.createDirect(directInput(data))
      : reservationsApi.create({ ...data, follows: previous.value?.id ?? null }),
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
        <button
          v-for="choice in choices"
          :key="choice.mode"
          type="button"
          class="choice"
          :class="choice.mode"
          @click="choose(choice.mode)"
        >
          <span class="choice-head">
            <span class="choice-icon"
              ><component :is="choice.icon" :size="22" :stroke-width="1.6"
            /></span>
            <ArrowRight class="go" :size="18" />
          </span>
          <strong>{{ choice.title }}</strong>
          <span class="muted">{{ choice.hint }}</span>
          <ul class="points">
            <li v-for="point in choice.points" :key="point">
              <Check :size="14" :stroke-width="2.2" />{{ point }}
            </li>
          </ul>
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
      <NAlert v-if="previous" type="info" :bordered="false" class="again">
        {{ t('reservations.again.prefilled', { number: previous.number }) }}
      </NAlert>
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
            :initial="initial"
            @submit="submit"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.again {
  margin-bottom: 14px;
}
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
  grid-template-columns: repeat(2, minmax(0, 400px));
  justify-content: center;
  gap: 16px;
}
.choice {
  --accent: var(--ar-primary);
  position: relative;
  display: grid;
  grid-template-rows: auto auto 1fr auto;
  align-content: start;
  gap: 8px;
  overflow: hidden;
  padding: 22px 24px 20px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  color: var(--ar-text-muted);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    box-shadow 0.15s ease,
    transform 0.15s ease;
}
.choice.direct {
  --accent: var(--ar-violet);
}
/* A strip in the mode's colour that fills in on hover. */
.choice::before {
  content: '';
  position: absolute;
  inset: 0 0 auto;
  height: 3px;
  background: var(--accent);
  transform: scaleX(0.18);
  transform-origin: left;
  transition: transform 0.25s ease;
}
.choice:hover,
.choice:focus-visible {
  border-color: color-mix(in srgb, var(--accent) 55%, var(--ar-border));
  box-shadow: 0 6px 20px -12px color-mix(in srgb, var(--accent) 60%, transparent);
  transform: translateY(-1px);
}
.choice:hover::before,
.choice:focus-visible::before {
  transform: scaleX(1);
}
.choice:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
.choice-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}
.choice-icon {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--accent) 12%, transparent);
  color: var(--accent);
}
.go {
  color: var(--ar-text-subtle);
  transition:
    transform 0.15s ease,
    color 0.15s ease;
}
.choice:hover .go,
.choice:focus-visible .go {
  color: var(--accent);
  transform: translateX(3px);
}
.choice strong {
  color: var(--ar-text);
  font-size: 16px;
  font-weight: 600;
}
.choice .muted {
  line-height: 1.5;
}
.points {
  display: grid;
  gap: 6px;
  margin: 8px 0 0;
  padding: 12px 0 0;
  border-top: 1px dashed var(--ar-border);
  list-style: none;
  font-size: 12.5px;
}
.points li {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  color: var(--ar-text);
}
.points svg {
  flex: none;
  margin-top: 2px;
  color: var(--accent);
}
@media (prefers-reduced-motion: reduce) {
  .choice,
  .choice::before,
  .go {
    transition: none;
  }
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
