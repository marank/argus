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
import { useLive } from '@/composables/useLive'
import type { Needs, AssetRequestNeed, ConsumableNeed } from '@/types/procurement'

const { t } = useI18n()
const { date } = useFormat()

const needs = ref<Needs | null>(null)
const loading = ref(false)
const selectedAssetRequests = ref<DataTableRowKey[]>([])
const selectedConsumables = ref<DataTableRowKey[]>([])
const showOrder = ref(false)

async function load() {
  loading.value = true
  try {
    needs.value = await needsApi.list()
    selectedAssetRequests.value = []
    selectedConsumables.value = []
  } finally {
    loading.value = false
  }
}
onMounted(load)
useLive(['request', 'order'], load, { paused: () => showOrder.value })

const num = (value: number, cls = '') => h('span', { class: `mono ${cls}` }, value)

const assetRequestColumns = computed<DataTableColumns<AssetRequestNeed>>(() => [
  { type: 'selection', disabled: (n) => n.to_order === 0 },
  {
    key: 'item',
    title: t('procurement.orders.item'),
    minWidth: 220,
    render: (n) =>
      h('div', [
        h('div', [
          n.asset_request_item.label,
          n.asset_request_item.is_free_text
            ? h('span', { class: 'free-tag' }, t('requests.freeText'))
            : null,
        ]),
        n.asset_request_item.default_supplier
          ? h('small', { class: 'muted' }, n.asset_request_item.default_supplier.name)
          : null,
      ]),
  },
  {
    key: 'request',
    title: t('nav.requests'),
    width: 260,
    render: (n) =>
      h('div', { class: 'row' }, [
        h(
          RouterLink,
          { to: { name: 'request', params: { id: n.asset_request.id } }, class: 'mono' },
          () => n.asset_request.number,
        ),
        h(StatusTag, { group: 'requestStatus', value: n.asset_request.status }),
      ]),
  },
  {
    key: 'requester',
    title: t('requests.requester'),
    width: 160,
    render: (n) => n.asset_request.requester.display_name,
  },
  {
    key: 'start',
    title: t('requests.startDate'),
    width: 110,
    render: (n) => h('span', { class: 'mono' }, date(n.asset_request.start_date)),
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

const consumableColumns = computed<DataTableColumns<ConsumableNeed>>(() => [
  { type: 'selection', disabled: (n) => n.to_order === 0 },
  {
    key: 'item',
    title: t('procurement.orders.item'),
    minWidth: 220,
    render: (n) => n.consumable.model.full_name,
  },
  {
    key: 'location',
    title: t('inventory.fields.location'),
    width: 200,
    render: (n) => n.consumable.location.full_name,
  },
  {
    key: 'qty',
    title: t('inventory.consumables.onHand'),
    width: 100,
    align: 'right',
    render: (n) => num(n.consumable.quantity),
  },
  {
    key: 'min',
    title: t('inventory.consumables.minimum'),
    width: 100,
    align: 'right',
    render: (n) => num(n.consumable.min_quantity, 'muted'),
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
  for (const n of needs.value?.requests ?? []) {
    if (!selectedAssetRequests.value.includes(n.asset_request_item.id)) continue
    lines.push({
      label: `${n.asset_request_item.label} · ${n.asset_request.number}`,
      asset_model: n.asset_request_item.asset_model?.id ?? null,
      category: n.asset_request_item.category?.id ?? null,
      quantity: n.to_order,
      asset_request_item: n.asset_request_item.id,
    })
  }
  for (const n of needs.value?.consumables ?? []) {
    if (!selectedConsumables.value.includes(n.consumable.id)) continue
    lines.push({
      label: n.consumable.model.full_name,
      asset_model: n.consumable.model.id,
      quantity: n.to_order,
    })
  }
  return lines
})

const defaultSupplier = computed(() => {
  const first = needs.value?.requests.find((n) =>
    selectedAssetRequests.value.includes(n.asset_request_item.id),
  )
  return (
    first?.asset_request_item.default_supplier?.id ??
    needs.value?.consumables.find((n) => selectedConsumables.value.includes(n.consumable.id))
      ?.consumable.default_supplier?.id ??
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
      <NCard :title="t('procurement.needs.fromRequests')" size="small">
        <EmptyState v-if="needs && !needs.requests.length" :text="t('procurement.needs.empty')" />
        <NDataTable
          v-else
          v-model:checked-row-keys="selectedAssetRequests"
          size="small"
          :columns="assetRequestColumns"
          :data="needs?.requests ?? []"
          :loading="loading"
          :row-key="(n: AssetRequestNeed) => n.asset_request_item.id"
          :scroll-x="1100"
        />
      </NCard>
      <NCard :title="t('procurement.needs.belowMinimum')" size="small">
        <EmptyState
          v-if="needs && !needs.consumables.length"
          :text="t('procurement.needs.empty')"
        />
        <NDataTable
          v-else
          v-model:checked-row-keys="selectedConsumables"
          size="small"
          :columns="consumableColumns"
          :data="needs?.consumables ?? []"
          :loading="loading"
          :row-key="(n: ConsumableNeed) => n.consumable.id"
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
