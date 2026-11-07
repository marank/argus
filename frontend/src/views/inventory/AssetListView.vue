<script setup lang="ts">
import type { Id } from '@/types/common'
import { modelLabel } from '@/utils/models'
import { FileUp, Layers, Plus, ScanBarcode } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { usersApi } from '@/api/accounts'
import { assetsApi } from '@/api/inventory'
import {
  assetModelsApi,
  categoriesApi,
  locationsApi,
  manufacturersApi,
  suppliersApi,
} from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import AssetFormDrawer from '@/components/inventory/AssetFormDrawer.vue'
import AssetImportModal from '@/components/inventory/AssetImportModal.vue'
import BulkCreateModal from '@/components/inventory/BulkCreateModal.vue'
import SeriesCreateModal from '@/components/inventory/SeriesCreateModal.vue'
import ListTable from '@/components/table/ListTable.vue'
import TableToolbar from '@/components/table/TableToolbar.vue'
import type { TableColumn, TableFilter, TableGrouping } from '@/components/table/types'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { useTableView } from '@/composables/useTableView'
import { ASSET_STATUSES } from '@/types/inventory'
import { categoryIcon } from '@/utils/icons'
import { useAuthStore } from '@/stores/auth'

type Asset = Schemas['AssetOut']

const { t } = useI18n()
// Without the right to change assets, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('assets', 'write'))
const route = useRoute()
const router = useRouter()
const { date, enumLabel, money } = useFormat()
/** Codes and numbers in the mono font; empty ones as a dash. */
const mono = (value: string | null | undefined) => h('span', { class: 'mono' }, value || '—')

// Links (dashboard, calendar, model page) preset filters; they show as filters that can be cleared.
const queryIds = (key: string) => [route.query[key] ?? []].flat().map(String)
const queryDate = (key: string) => (route.query[key] ? String(route.query[key]) : null)

const columns = computed<TableColumn<Asset>[]>(() => [
  {
    key: 'inventory_number',
    title: t('inventory.fields.inventoryNumber'),
    sorter: true,
    width: 130,
    fixed: 'left',
    hideable: false,
    render: (a) => h('span', { class: 'mono strong' }, a.inventory_number),
  },
  {
    key: 'model__name',
    title: t('inventory.fields.model'),
    sorter: true,
    minWidth: 220,
    render: (a) =>
      h('div', { class: 'model-cell' }, [
        h(categoryIcon(a.category.icon), { size: 15, class: 'muted' }),
        h('div', [h('div', a.model.full_name), h('small', { class: 'muted' }, a.category.name)]),
      ]),
  },
  {
    key: 'serial_number',
    title: t('inventory.fields.serialNumber'),
    sorter: true,
    width: 150,
    render: (a) => h('span', { class: 'mono' }, a.serial_number || '—'),
  },
  {
    key: 'identifier',
    hidden: true,
    title: t('inventory.fields.identifier'),
    sorter: true,
    width: 170,
    render: (a) =>
      a.identifier
        ? h(
            'span',
            { class: 'mono', title: a.category.identifier_label || undefined },
            a.identifier,
          )
        : '—',
  },
  {
    key: 'status',
    title: t('common.status'),
    sorter: true,
    width: 140,
    render: (a) => h(StatusTag, { group: 'assetStatus', value: a.status }),
  },
  {
    key: 'assigned_to__last_name',
    title: t('inventory.fields.assignedTo'),
    sorter: true,
    width: 170,
    render: (a) =>
      a.assigned_to?.display_name ??
      // Set aside, not yet handed out: for whom and with which request.
      (a.reserved_for
        ? h('span', { class: 'muted' }, [
            t('inventory.reservedFor', { name: a.reserved_for.requester.display_name }),
            h('small', { class: 'mono reserved-number' }, a.reserved_for.number),
          ])
        : '—'),
  },
  {
    key: 'location__name',
    title: t('inventory.fields.location'),
    sorter: true,
    width: 190,
    ellipsis: { tooltip: true },
    render: (a) => a.location?.full_name ?? '—',
  },
  {
    key: 'warranty_until',
    title: t('inventory.fields.warrantyUntil'),
    sorter: true,
    width: 120,
    render: (a) => h('span', { class: 'mono' }, date(a.warranty_until)),
  },
  // Further columns to show from the column settings.
  {
    key: 'manufacturer',
    title: t('inventory.fields.manufacturer'),
    hidden: true,
    width: 150,
    render: (a) => a.manufacturer.name,
  },
  {
    key: 'model__category__name',
    title: t('inventory.fields.category'),
    sorter: true,
    hidden: true,
    width: 150,
    render: (a) => a.category.name,
  },
  {
    key: 'condition',
    title: t('inventory.fields.condition'),
    hidden: true,
    width: 110,
    render: (a) => enumLabel('condition', a.condition),
  },
  {
    key: 'hostname',
    title: t('inventory.fields.hostname'),
    hidden: true,
    width: 150,
    render: (a) => mono(a.hostname),
  },
  {
    key: 'imei',
    title: t('inventory.fields.imei'),
    hidden: true,
    width: 160,
    render: (a) => mono(a.imei),
  },
  {
    key: 'mac_address',
    title: t('inventory.fields.macAddress'),
    hidden: true,
    width: 160,
    render: (a) => mono(a.mac_address),
  },
  {
    key: 'parent',
    title: t('inventory.fields.parent'),
    hidden: true,
    width: 130,
    render: (a) => mono(a.parent?.inventory_number),
  },
  {
    key: 'assigned_since',
    title: t('inventory.fields.assignedSince'),
    hidden: true,
    width: 120,
    render: (a) => mono(date(a.assigned_since)),
  },
  {
    key: 'is_loanable',
    title: t('inventory.fields.loanable'),
    hidden: true,
    width: 110,
    render: (a) => (a.is_loanable ? t('common.yes') : '—'),
  },
  {
    key: 'supplier',
    title: t('inventory.fields.supplier'),
    hidden: true,
    width: 160,
    render: (a) => a.supplier?.name ?? '—',
  },
  {
    key: 'purchase_date',
    title: t('inventory.fields.purchaseDate'),
    sorter: true,
    hidden: true,
    width: 120,
    render: (a) => mono(date(a.purchase_date)),
  },
  {
    key: 'purchase_price',
    title: t('inventory.fields.purchasePrice'),
    hidden: true,
    width: 120,
    align: 'right',
    render: (a) => mono(money(a.purchase_price)),
  },
  {
    key: 'notes',
    title: t('common.notes'),
    hidden: true,
    width: 220,
    ellipsis: { tooltip: true },
    render: (a) => a.notes || '—',
  },
  {
    key: 'created_at',
    title: t('common.createdAt'),
    sorter: true,
    hidden: true,
    width: 120,
    render: (a) => mono(date(a.created_at)),
  },
  {
    key: 'updated_at',
    title: t('common.updatedAt'),
    hidden: true,
    width: 120,
    render: (a) => mono(date(a.updated_at)),
  },
])

const without = (field: string) =>
  h('span', { class: 'muted' }, t('table.without', { name: field }))

const groupings = (): TableGrouping<Asset>[] => [
  {
    key: 'category',
    label: t('inventory.fields.category'),
    ordering: 'model__category__sort_order,model__category__name',
    rowKey: (a) => a.category.id,
    rowLabel: (a) => [h(categoryIcon(a.category.icon), { size: 14 }), a.category.name],
  },
  {
    key: 'status',
    label: t('common.status'),
    ordering: 'status',
    rowKey: (a) => a.status,
    rowLabel: (a) => h(StatusTag, { group: 'assetStatus', value: a.status }),
  },
  {
    key: 'model',
    label: t('inventory.fields.model'),
    ordering: 'model__manufacturer__name,model__name,model_id',
    rowKey: (a) => a.model.id,
    rowLabel: (a) => [h(categoryIcon(a.category.icon), { size: 14 }), a.model.full_name],
  },
  {
    key: 'location',
    label: t('inventory.fields.location'),
    ordering: 'location__name,location_id',
    rowKey: (a) => a.location?.id ?? '',
    rowLabel: (a) => a.location?.full_name ?? without(t('inventory.fields.location')),
  },
  {
    key: 'assigned_to',
    label: t('inventory.fields.assignedTo'),
    ordering: 'assigned_to__last_name,assigned_to__first_name,assigned_to_id',
    rowKey: (a) => a.assigned_to?.id ?? '',
    rowLabel: (a) => a.assigned_to?.display_name ?? without(t('inventory.fields.assignedTo')),
  },
]

const filters = computed<TableFilter[]>(() => [
  {
    key: 'status',
    label: t('common.status'),
    type: 'select',
    options: ASSET_STATUSES.map((s) => ({ value: s, label: enumLabel('assetStatus', s) })),
  },
  {
    key: 'category',
    label: t('inventory.fields.category'),
    type: 'entity',
    fetcher: categoriesApi.list,
    params: { kind: 'hardware' },
    display: (c: Schemas['CategoryOut']) => c.path.join(' / '),
  },
  {
    key: 'model',
    label: t('inventory.fields.model'),
    type: 'entity',
    fetcher: assetModelsApi.list,
    params: { tracking: 'serialized' },
    display: modelLabel,
  },
  {
    key: 'location',
    label: t('inventory.fields.location'),
    type: 'entity',
    fetcher: locationsApi.list,
    display: (l: Schemas['LocationOut']) => l.full_name,
  },
  {
    key: 'assigned_to',
    label: t('inventory.fields.assignedTo'),
    type: 'entity',
    fetcher: usersApi.list,
    display: (u: Schemas['UserOut']) => u.display_name,
  },
  {
    key: 'manufacturer',
    label: t('inventory.fields.manufacturer'),
    type: 'entity',
    fetcher: manufacturersApi.list,
    display: (m: Schemas['ManufacturerOut']) => m.name,
  },
  {
    key: 'supplier',
    label: t('inventory.fields.supplier'),
    type: 'entity',
    fetcher: suppliersApi.list,
    display: (s: Schemas['SupplierOut']) => s.name,
  },
  { key: 'is_loanable', label: t('inventory.fields.loanable'), type: 'toggle', on: () => true },
  {
    key: 'purchase_date',
    label: t('inventory.fields.purchaseDate'),
    type: 'daterange',
    from: 'purchase_from',
    until: 'purchase_until',
  },
  {
    key: 'warranty',
    label: t('inventory.fields.warrantyUntil'),
    type: 'daterange',
    from: 'warranty_from',
    until: 'warranty_until',
  },
])

const view = useTableView<Asset>({
  id: 'assets',
  columns: (): TableColumn<Asset>[] => columns.value,
  rows: (): Asset[] => list.rows.value,
  groupings,
  defaultGrouping: 'category',
})

const list = useList(assetsApi.list, {
  live: ['asset'],
  ordering: 'inventory_number',
  groupOrdering: view.groupOrdering,
  filters: {
    status: queryIds('status'),
    category: queryIds('category'),
    model: queryIds('model'),
    location: [],
    assigned_to: [],
    manufacturer: [],
    supplier: [],
    is_loanable: null,
    warranty_from: queryDate('warranty_from'),
    warranty_until: queryDate('warranty_until'),
    purchase_from: null,
    purchase_until: null,
  },
})
onMounted(list.load)

const showForm = ref(false)
const showBulk = ref(false)
const showSeries = ref(false)
const showImport = ref(false)

const openAsset = (a: Asset) => router.push({ name: 'asset', params: { id: a.id } })

function onSaved(asset: { id: Id }) {
  router.push({ name: 'asset', params: { id: asset.id } })
}
</script>

<template>
  <div class="page">
    <PageHeader :title="t('inventory.assets')" :subtitle="t('inventory.assetsSubtitle')">
      <template v-if="canWrite" #actions>
        <NButton @click="showImport = true">
          <template #icon><FileUp :size="16" /></template>
          {{ t('inventory.importAssets') }}
        </NButton>
        <NButton @click="showBulk = true">
          <template #icon><ScanBarcode :size="16" /></template>
          {{ t('inventory.bulkCreate') }}
        </NButton>
        <NButton @click="showSeries = true">
          <template #icon><Layers :size="16" /></template>
          {{ t('inventory.seriesCreate') }}
        </NButton>
        <NButton type="primary" @click="showForm = true">
          <template #icon><Plus :size="16" /></template>
          {{ t('inventory.newAsset') }}
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
      <ListTable :view="view" :list="list" @row-click="openAsset" />
    </div>

    <AssetFormDrawer v-model:show="showForm" @saved="onSaved" />
    <BulkCreateModal v-model:show="showBulk" @created="list.reload" />
    <SeriesCreateModal v-model:show="showSeries" @created="list.reload" />
    <AssetImportModal v-model:show="showImport" @imported="list.reload" />
  </div>
</template>

<style scoped>
:deep(.model-cell) {
  display: flex;
  align-items: center;
  gap: 10px;
}
:deep(.strong) {
  font-weight: 600;
}
:deep(.reserved-number) {
  display: block;
  font-size: 11px;
}
</style>
