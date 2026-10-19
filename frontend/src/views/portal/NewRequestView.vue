<script setup lang="ts">
import { NSkeleton } from 'naive-ui'
import { watchDebounced } from '@vueuse/core'
import { computed, onMounted, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { portalApi, reservationsApi } from '@/api/reservations'
import PageHeader from '@/components/common/PageHeader.vue'
import CatalogBrowser from '@/components/reservations/request/CatalogBrowser.vue'
import ConsumableQuickPick from '@/components/reservations/request/ConsumableQuickPick.vue'
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
import type {
  CatalogCategory,
  CatalogModel,
  MyConsumables,
  ReservationInput,
} from '@/types/reservations'

const { t } = useI18n()
const features = useFeaturesStore()
const router = useRouter()
const auth = useAuthStore()
const { busy, run } = useAction()

const catalog = ref<CatalogCategory[] | null>(null)
const cart = ref<CartLine[]>([])
const myConsumables = ref<MyConsumables[]>([])

const today = new Date().setHours(0, 0, 0, 0)
const period = reactive<RequestPeriod>({
  duration: 'temporary',
  // Suggested period from the site settings (default loan period, start day included).
  range: [today, today + (features.rules.default_loan_days - 1) * 86400000],
  start: today,
})

onMounted(async () => {
  // The quick pick can be switched off; its endpoint is gone then.
  const [entries, consumables] = await Promise.all([
    portalApi.catalog(periodQuery(period)),
    features.isOn('consumable_quick_pick') ? portalApi.myConsumables() : Promise.resolve([]),
  ])
  catalog.value = entries
  myConsumables.value = consumables
})

/** Lookup of what is free in the period, by cart/option key. */
function availableFor(key: string): number | null {
  for (const category of catalog.value ?? []) {
    if (key === optionKey(category)) return category.available
    const model = category.models.find((m) => key === optionKey(category, m))
    if (model) return model.available
  }
  return null
}

// IT sees availability for the chosen period: refresh the counts when it changes.
let latestQuery = 0
watchDebounced(
  () => periodQuery(period),
  async (query) => {
    if (!auth.isItStaff || !catalog.value) return
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

async function submit(data: ReservationInput) {
  const reservation = await run(() => reservationsApi.create(data))
  if (reservation) {
    router.push({ name: 'portal-request', params: { id: reservation.id }, query: { created: '1' } })
  }
}
</script>

<template>
  <div class="page">
    <PageHeader :title="t('reservations.new.title')" :subtitle="t('reservations.new.subtitle')" />
    <div class="layout">
      <NSkeleton v-if="!catalog" height="320px" />
      <CatalogBrowser
        v-else
        :catalog="catalog"
        :cart-counts="cartCounts"
        @add="add"
        @add-free-text="addFreeText"
      >
        <ConsumableQuickPick
          :groups="myConsumables"
          :catalog="catalog"
          :cart-counts="cartCounts"
          @add="add"
        />
      </CatalogBrowser>
      <div class="side">
        <RequestPeriodCard v-model="period" :shows-availability="auth.isItStaff" />
        <RequestCart
          v-model:lines="cart"
          :period="period"
          :busy="busy"
          :can-choose-requester="auth.isItStaff"
          :requester-placeholder="auth.user?.display_name"
          @submit="submit"
        />
      </div>
    </div>
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
@media (max-width: 1080px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .side {
    position: static;
  }
}
</style>
