<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { computed, h, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { suppliersApi } from '@/api/masterdata'
import { ordersApi } from '@/api/procurement'
import type { Schemas } from '@/api/types'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ListTable from '@/components/table/ListTable.vue'
import TableToolbar from '@/components/table/TableToolbar.vue'
import type { TableColumn, TableFilter, TableGrouping } from '@/components/table/types'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { useTableView } from '@/composables/useTableView'
import { ORDER_STATUSES } from '@/types/procurement'
import { useAuthStore } from '@/stores/auth'
import { isPast } from '@/utils/requests'

const { t } = useI18n()
// Without the right to change procurement, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('procurement', 'write'))
const route = useRoute()
const router = useRouter()
const { date, money, enumLabel } = useFormat()
const { busy, run } = useAction()

type Order = Schemas['PurchaseOrderListOut']

/** Placed but not (fully) received after the expected day. */
const late = (o: Schemas['PurchaseOrderListOut']) =>
  ['ordered', 'partially_received'].includes(o.status) && isPast(o.expected_date)

const filters = computed<TableFilter[]>(() => [
  {
    key: 'status',
    label: t('common.status'),
    type: 'select',
    options: ORDER_STATUSES.map((s) => ({ value: s, label: enumLabel('orderStatus', s) })),
  },
  {
    key: 'supplier',
    label: t('procurement.orders.supplier'),
    type: 'entity',
    fetcher: suppliersApi.list,
    display: (s: Schemas['SupplierOut']) => s.name,
  },
  {
    key: 'order_date',
    label: t('procurement.orders.orderDate'),
    type: 'daterange',
    from: 'ordered_from',
    until: 'ordered_until',
  },
  {
    key: 'expected_date',
    label: t('procurement.orders.expectedDate'),
    type: 'daterange',
    from: 'expected_from',
    until: 'expected_until',
  },
])

const groupings = (): TableGrouping<Order>[] => [
  {
    key: 'status',
    label: t('common.status'),
    ordering: 'status',
    rowKey: (o) => o.status,
    rowLabel: (o) => h(StatusTag, { group: 'orderStatus', value: o.status }),
  },
  {
    key: 'supplier',
    label: t('procurement.orders.supplier'),
    ordering: 'supplier__name,supplier_id',
    rowKey: (o) => o.supplier?.id ?? '',
    rowLabel: (o) =>
      o.supplier?.name ??
      h('span', { class: 'muted' }, t('table.without', { name: t('procurement.orders.supplier') })),
  },
]

const columns = computed<TableColumn<Order>[]>(() => [
  {
    key: 'number',
    title: t('procurement.orders.number'),
    sorter: true,
    hideable: false,
    width: 140,
    render: (o) => h('span', { class: 'mono strong' }, o.number),
  },
  {
    key: 'supplier',
    title: t('procurement.orders.supplier'),
    minWidth: 180,
    render: (o) => o.supplier?.name ?? '—',
  },
  {
    key: 'supplier_reference',
    hidden: true,
    title: t('procurement.orders.supplierReference'),
    width: 160,
    render: (o) => h('span', { class: 'mono' }, o.supplier_reference || '—'),
  },
  {
    key: 'line_count',
    hidden: true,
    title: t('procurement.orders.lines'),
    width: 90,
    align: 'right',
    render: (o) => h('span', { class: 'mono' }, o.line_count),
  },
  {
    key: 'total',
    title: t('common.total'),
    width: 120,
    align: 'right',
    render: (o) => h('span', { class: 'mono' }, money(o.total)),
  },
  {
    key: 'order_date',
    title: t('procurement.orders.orderDate'),
    sorter: true,
    width: 120,
    render: (o) => h('span', { class: 'mono' }, date(o.order_date)),
  },
  {
    key: 'expected_date',
    title: t('procurement.orders.expectedDate'),
    sorter: true,
    width: 120,
    render: (o) =>
      late(o)
        ? h('span', { class: 'mono late', title: t('procurement.orders.late') }, [
            date(o.expected_date),
          ])
        : h('span', { class: 'mono' }, date(o.expected_date)),
  },
  {
    key: 'status',
    title: t('common.status'),
    sorter: true,
    width: 160,
    render: (o) => h(StatusTag, { group: 'orderStatus', value: o.status }),
  },
  // Further columns to show from the column settings.
  {
    key: 'created_at',
    title: t('common.createdAt'),
    sorter: true,
    hidden: true,
    width: 120,
    render: (o) => h('span', { class: 'mono' }, date(o.created_at)),
  },
])

async function createEmpty() {
  const order = await run(() =>
    ordersApi.create({
      supplier: null,
      expected_date: null,
      supplier_reference: '',
      delivery_location: null,
      notes: '',
      lines: [{ asset_model: null, description: '—', quantity: 1, unit_price: null }],
    }),
  )
  if (order) router.push({ name: 'order', params: { id: order.id } })
}

const view = useTableView<Order>({
  id: 'orders',
  columns: (): TableColumn<Order>[] => columns.value,
  rows: (): Order[] => list.rows.value,
  groupings,
})

const list = useList(ordersApi.list, {
  live: ['order'],
  ordering: '-created_at',
  groupOrdering: view.groupOrdering,
  filters: {
    status: route.query.status
      ? route.query.status === 'ordered'
        ? ['ordered', 'partially_received']
        : [String(route.query.status)]
      : [],
    supplier: [],
    ordered_from: null,
    ordered_until: null,
    expected_from: null,
    expected_until: null,
  },
})
onMounted(list.load)
</script>

<template>
  <div class="page">
    <PageHeader :title="t('procurement.orders.title')" :subtitle="t('procurement.orders.subtitle')">
      <template v-if="canWrite" #actions>
        <NButton type="primary" :loading="busy" @click="createEmpty">
          <template #icon><Plus :size="16" /></template>
          {{ t('procurement.orders.new') }}
        </NButton>
      </template>
    </PageHeader>
    <div class="stack">
      <TableToolbar
        v-model:search="list.search.value"
        :list="list"
        :filters="filters"
        :view="view"
      />
      <ListTable
        :view="view"
        :list="list"
        @row-click="(o: Order) => router.push({ name: 'order', params: { id: o.id } })"
      />
    </div>
  </div>
</template>

<style scoped>
:deep(.strong) {
  font-weight: 600;
}
:deep(.late) {
  color: var(--ar-error);
}
</style>
