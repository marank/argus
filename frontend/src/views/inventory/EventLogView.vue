<script setup lang="ts">
import { computed, h, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { eventsApi } from '@/api/inventory'
import { assetModelsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'
import PageHeader from '@/components/common/PageHeader.vue'
import ListTable from '@/components/table/ListTable.vue'
import TableToolbar from '@/components/table/TableToolbar.vue'
import type { TableColumn, TableFilter, TableGrouping } from '@/components/table/types'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { useTableView } from '@/composables/useTableView'
import { modelLabel } from '@/utils/models'

type AssetEvent = Schemas['AssetEventWithAssetOut']

const { t } = useI18n()
const { dateTime, enumLabel, money } = useFormat()

const ALL_KINDS = allValues<Schemas['AssetEventKind']>({
  component_replaced: true,
  repair: true,
  maintenance: true,
  inspection: true,
  note: true,
  assigned: true,
  returned: true,
  reserved: true,
  replaced: true,
  status_changed: true,
  created: true,
  issue_reported: true,
  issue_resolved: true,
})

const filters = computed<TableFilter[]>(() => [
  {
    key: 'kind',
    label: t('inventory.event.kind'),
    type: 'select',
    options: ALL_KINDS.map((k) => ({ value: k, label: enumLabel('eventKind', k) })),
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
    key: 'occurred_at',
    label: t('inventory.event.occurredAt'),
    type: 'daterange',
    from: 'since',
    until: 'until',
  },
])

const groupings = (): TableGrouping<AssetEvent>[] => [
  {
    key: 'kind',
    label: t('inventory.event.kind'),
    ordering: 'kind',
    rowKey: (e) => e.kind,
    rowLabel: (e) => enumLabel('eventKind', e.kind),
  },
  {
    key: 'model',
    label: t('inventory.fields.model'),
    ordering: 'asset__model__name,asset__model_id',
    rowKey: (e) => e.asset.model.id,
    rowLabel: (e) => e.asset.model.full_name,
  },
  {
    key: 'performed_by',
    label: t('inventory.event.performedBy'),
    ordering: 'performed_by__last_name,performed_by_id',
    rowKey: (e) => e.performed_by?.id ?? '',
    rowLabel: (e) =>
      e.performed_by?.display_name ??
      h('span', { class: 'muted' }, t('table.without', { name: t('inventory.event.performedBy') })),
  },
]

const columns = computed<TableColumn<AssetEvent>[]>(() => [
  {
    key: 'occurred_at',
    title: t('inventory.event.occurredAt'),
    sorter: true,
    width: 150,
    render: (e) => h('span', { class: 'mono' }, dateTime(e.occurred_at)),
  },
  {
    key: 'asset__inventory_number',
    title: t('inventory.event.asset'),
    sorter: true,
    width: 260,
    render: (e) =>
      h('div', [
        h(
          RouterLink,
          { to: { name: 'asset', params: { id: e.asset.id } }, class: 'mono' },
          () => e.asset.inventory_number,
        ),
        h('small', { class: 'muted', style: 'display:block' }, e.asset.model.full_name),
      ]),
  },
  {
    key: 'kind',
    title: t('inventory.event.kind'),
    sorter: true,
    width: 170,
    render: (e) => enumLabel('eventKind', e.kind),
  },
  {
    key: 'component',
    title: t('inventory.event.component'),
    width: 170,
    render: (e) => e.component_type?.name || e.component || '—',
  },
  {
    key: 'description',
    title: t('common.description'),
    minWidth: 180,
    ellipsis: { tooltip: true },
    render: (e) => e.description || e.related_user?.display_name || '—',
  },
  {
    key: 'cost',
    title: t('inventory.event.cost'),
    sorter: true,
    width: 100,
    align: 'right',
    render: (e) => h('span', { class: 'mono' }, money(e.cost)),
  },
  {
    key: 'performed_by',
    title: t('inventory.event.performedBy'),
    width: 140,
    render: (e) => e.performed_by?.display_name ?? '—',
  },
  // Further columns to show from the column settings.
  {
    key: 'serial_number',
    title: t('inventory.fields.serialNumber'),
    hidden: true,
    width: 150,
    render: (e) => h('span', { class: 'mono' }, e.asset.serial_number || '—'),
  },
  {
    key: 'component_serial',
    title: t('inventory.event.componentSerial'),
    hidden: true,
    width: 160,
    render: (e) => h('span', { class: 'mono' }, e.component_serial || '—'),
  },
  {
    key: 'previous_serial',
    title: t('inventory.event.previousSerial'),
    hidden: true,
    width: 160,
    render: (e) => h('span', { class: 'mono' }, e.previous_serial || '—'),
  },
  {
    key: 'related_user',
    title: t('inventory.event.employee'),
    hidden: true,
    width: 160,
    render: (e) => e.related_user?.display_name ?? '—',
  },
  {
    key: 'asset_request',
    title: t('requests.number'),
    hidden: true,
    width: 140,
    render: (e) =>
      e.asset_request
        ? h(
            RouterLink,
            { to: { name: 'request', params: { id: e.asset_request.id } }, class: 'mono' },
            () => e.asset_request!.number,
          )
        : '—',
  },
])

const view = useTableView<AssetEvent>({
  id: 'events',
  columns: (): TableColumn<AssetEvent>[] => columns.value,
  rows: (): AssetEvent[] => list.rows.value,
  groupings,
})

const list = useList(eventsApi.list, {
  live: ['asset'],
  ordering: '-occurred_at',
  groupOrdering: view.groupOrdering,
  filters: {
    kind: ['component_replaced', 'repair', 'maintenance', 'inspection'],
    model: [],
    since: null,
    until: null,
  },
})
onMounted(list.load)
</script>

<template>
  <div class="page">
    <PageHeader :title="t('inventory.eventLog')" :subtitle="t('inventory.eventLogSubtitle')" />
    <div class="stack">
      <TableToolbar
        v-model:search="list.search.value"
        :list="list"
        :filters="filters"
        :view="view"
      />
      <ListTable :view="view" :list="list" />
    </div>
  </div>
</template>
