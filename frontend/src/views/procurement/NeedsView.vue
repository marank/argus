<script setup lang="ts">
import { RefreshCw, ShoppingCart } from '@lucide/vue'
import { NButton, NCard, NDataTable, type DataTableColumns, type DataTableRowKey } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { needsApi } from '@/api/procurement'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import CreateOrderModal, { type DraftLine } from '@/components/procurement/CreateOrderModal.vue'
import { useFormat } from '@/composables/useFormat'
import type { Needs, ReservationNeed, StockNeed } from '@/types/procurement'

const { t } = useI18n()
const { date } = useFormat()

const needs = ref<Needs | null>(null)
const loading = ref(false)
const selectedReservations = ref<DataTableRowKey[]>([])
const selectedStock = ref<DataTableRowKey[]>([])
const showOrder = ref(false)

async function load() {
  loading.value = true
  try {
    needs.value = await needsApi.list()
    selectedReservations.value = []
    selectedStock.value = []
  } finally {
    loading.value = false
  }
}
onMounted(load)

const num = (value: number, cls = '') => h('span', { class: `mono ${cls}` }, value)

const reservationColumns = computed<DataTableColumns<ReservationNeed>>(() => [
  { type: 'selection', disabled: (n) => n.to_order === 0 },
  {
    key: 'item',
    title: t('procurement.orders.item'),
    minWidth: 220,
    render: (n) =>
      h('div', [
        h('div', [
          n.reservation_item.label,
          n.reservation_item.is_free_text
            ? h('span', { class: 'free-tag' }, t('reservations.freeText'))
            : null,
        ]),
        n.reservation_item.default_supplier
          ? h('small', { class: 'muted' }, n.reservation_item.default_supplier.name)
          : null,
      ]),
  },
  {
    key: 'reservation',
    title: t('nav.reservations'),
    width: 260,
    render: (n) =>
      h('div', { class: 'row' }, [
        h(
          RouterLink,
          { to: { name: 'reservation', params: { id: n.reservation.id } }, class: 'mono' },
          () => n.reservation.number,
        ),
        h(StatusTag, { group: 'reservationStatus', value: n.reservation.status }),
      ]),
  },
  {
    key: 'requester',
    title: t('reservations.requester'),
    width: 160,
    render: (n) => n.reservation.requester.display_name,
  },
  {
    key: 'start',
    title: t('reservations.startDate'),
    width: 110,
    render: (n) => h('span', { class: 'mono' }, date(n.reservation.start_date)),
  },
  {
    key: 'missing',
    title: t('procurement.needs.missing'),
    width: 80,
    align: 'right',
    render: (n) => num(n.missing),
  },
  {
    key: 'available',
    title: t('procurement.needs.available'),
    width: 80,
    align: 'right',
    render: (n) => num(n.available, 'muted'),
  },
  {
    key: 'on_order',
    title: t('procurement.needs.onOrder'),
    width: 90,
    align: 'right',
    render: (n) => num(n.on_order, 'muted'),
  },
  {
    key: 'to_order',
    title: t('procurement.needs.toOrder'),
    width: 100,
    align: 'right',
    render: (n) => num(n.to_order, n.to_order ? 'todo' : 'muted'),
  },
])

const stockColumns = computed<DataTableColumns<StockNeed>>(() => [
  { type: 'selection', disabled: (n) => n.to_order === 0 },
  {
    key: 'item',
    title: t('procurement.orders.item'),
    minWidth: 220,
    render: (n) => n.stock_item.model.full_name,
  },
  {
    key: 'location',
    title: t('inventory.fields.location'),
    width: 200,
    render: (n) => n.stock_item.location.full_name,
  },
  {
    key: 'qty',
    title: t('inventory.stock.onHand'),
    width: 100,
    align: 'right',
    render: (n) => num(n.stock_item.quantity),
  },
  {
    key: 'min',
    title: t('inventory.stock.minimum'),
    width: 100,
    align: 'right',
    render: (n) => num(n.stock_item.min_quantity, 'muted'),
  },
  {
    key: 'on_order',
    title: t('procurement.needs.onOrder'),
    width: 90,
    align: 'right',
    render: (n) => num(n.on_order, 'muted'),
  },
  {
    key: 'to_order',
    title: t('procurement.needs.toOrder'),
    width: 100,
    align: 'right',
    render: (n) => num(n.to_order, n.to_order ? 'todo' : 'muted'),
  },
])

const draftLines = computed<DraftLine[]>(() => {
  const lines: DraftLine[] = []
  for (const n of needs.value?.reservations ?? []) {
    if (!selectedReservations.value.includes(n.reservation_item.id)) continue
    lines.push({
      label: `${n.reservation_item.label} · ${n.reservation.number}`,
      asset_model: n.reservation_item.asset_model?.id ?? null,
      category: n.reservation_item.category?.id ?? null,
      quantity: n.to_order,
      reservation_item: n.reservation_item.id,
    })
  }
  for (const n of needs.value?.stock ?? []) {
    if (!selectedStock.value.includes(n.stock_item.id)) continue
    lines.push({
      label: n.stock_item.model.full_name,
      asset_model: n.stock_item.model.id,
      quantity: n.to_order,
    })
  }
  return lines
})

const defaultSupplier = computed(() => {
  const first = needs.value?.reservations.find((n) =>
    selectedReservations.value.includes(n.reservation_item.id),
  )
  return (
    first?.reservation_item.default_supplier?.id ??
    needs.value?.stock.find((n) => selectedStock.value.includes(n.stock_item.id))?.stock_item
      .default_supplier?.id ??
    null
  )
})
</script>

<template>
  <div class="page">
    <PageHeader :title="t('procurement.needs.title')" :subtitle="t('procurement.needs.subtitle')">
      <template #actions>
        <NButton :loading="loading" @click="load">
          <template #icon><RefreshCw :size="15" /></template>
          {{ t('common.refresh') }}
        </NButton>
        <NButton type="primary" :disabled="!draftLines.length" @click="showOrder = true">
          <template #icon><ShoppingCart :size="15" /></template>
          {{ t('procurement.needs.createOrder') }} ({{ draftLines.length }})
        </NButton>
      </template>
    </PageHeader>
    <div class="stack">
      <p class="muted">{{ t('procurement.needs.selectHint') }}</p>
      <NCard :title="t('procurement.needs.fromReservations')" size="small">
        <EmptyState
          v-if="needs && !needs.reservations.length"
          :text="t('procurement.needs.empty')"
        />
        <NDataTable
          v-else
          v-model:checked-row-keys="selectedReservations"
          size="small"
          :columns="reservationColumns"
          :data="needs?.reservations ?? []"
          :loading="loading"
          :row-key="(n: ReservationNeed) => n.reservation_item.id"
          :scroll-x="1100"
        />
      </NCard>
      <NCard :title="t('procurement.needs.lowStock')" size="small">
        <EmptyState v-if="needs && !needs.stock.length" :text="t('procurement.needs.empty')" />
        <NDataTable
          v-else
          v-model:checked-row-keys="selectedStock"
          size="small"
          :columns="stockColumns"
          :data="needs?.stock ?? []"
          :loading="loading"
          :row-key="(n: StockNeed) => n.stock_item.id"
          :scroll-x="900"
        />
      </NCard>
    </div>
    <CreateOrderModal v-model:show="showOrder" :lines="draftLines" :supplier="defaultSupplier" />
  </div>
</template>

<style scoped>
:deep(.free-tag) {
  margin-left: 6px;
  padding: 0 5px;
  border: 1px solid var(--ar-warning);
  border-radius: 2px;
  color: var(--ar-warning);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
}
:deep(.todo) {
  color: var(--ar-warning);
  font-weight: 700;
}
</style>
