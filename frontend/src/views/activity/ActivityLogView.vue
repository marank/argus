<script setup lang="ts">
import { computed, h, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { usersApi } from '@/api/accounts'
import { activityApi } from '@/api/activity'
import PageHeader from '@/components/common/PageHeader.vue'
import ListTable from '@/components/table/ListTable.vue'
import TableToolbar from '@/components/table/TableToolbar.vue'
import type { TableColumn, TableFilter, TableGrouping } from '@/components/table/types'
import { useActivity } from '@/composables/useActivity'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { useTableView } from '@/composables/useTableView'
import { ACTIVITY_AREAS, ACTIVITY_KINDS, activityTarget, type Activity } from '@/types/activity'

const { t } = useI18n()
const { dateTime, enumLabel } = useFormat()
const { summary } = useActivity()

const filters = computed<TableFilter[]>(() => [
  {
    key: 'area',
    label: t('activity.area'),
    type: 'select',
    options: ACTIVITY_AREAS.map((a) => ({ value: a, label: enumLabel('activityArea', a) })),
  },
  {
    key: 'kind',
    label: t('activity.kind'),
    type: 'select',
    options: ACTIVITY_KINDS.map((k) => ({ value: k, label: enumLabel('activityKind', k) })),
  },
  {
    key: 'actor',
    label: t('activity.actor'),
    type: 'entity',
    fetcher: usersApi.list,
    params: { is_staff: true },
    display: (u: { display_name: string }) => u.display_name,
  },
  {
    key: 'occurred_at',
    label: t('activity.occurredAt'),
    type: 'daterange',
    from: 'since',
    until: 'until',
  },
])

const groupings = (): TableGrouping<Activity>[] => [
  {
    key: 'area',
    label: t('activity.area'),
    ordering: 'area',
    rowKey: (a) => a.area,
    rowLabel: (a) => enumLabel('activityArea', a.area),
  },
  {
    key: 'actor',
    label: t('activity.actor'),
    ordering: 'actor__last_name,actor_id',
    rowKey: (a) => a.actor?.id ?? '',
    rowLabel: (a) =>
      a.actor?.display_name ??
      h('span', { class: 'muted' }, t('table.without', { name: t('activity.actor') })),
  },
]

const subject = (a: Activity) => {
  const to = activityTarget(a)
  return to ? h(RouterLink, { to }, () => a.subject_label) : a.subject_label
}

const columns = computed<TableColumn<Activity>[]>(() => [
  {
    key: 'occurred_at',
    title: t('activity.occurredAt'),
    sorter: true,
    width: 150,
    render: (a) => h('span', { class: 'mono' }, dateTime(a.occurred_at)),
  },
  {
    key: 'area',
    title: t('activity.area'),
    sorter: true,
    width: 150,
    render: (a) => enumLabel('activityArea', a.area),
  },
  {
    key: 'subject_label',
    title: t('activity.object'),
    sorter: true,
    minWidth: 220,
    ellipsis: { tooltip: true },
    render: subject,
  },
  {
    key: 'kind',
    title: t('activity.kind'),
    sorter: true,
    width: 230,
    render: (a) => summary(a),
  },
  {
    key: 'actor',
    title: t('activity.actor'),
    width: 150,
    render: (a) => a.actor?.display_name ?? '—',
  },
  {
    key: 'related_user',
    title: t('activity.employee'),
    width: 150,
    render: (a) => a.related_user?.display_name ?? '—',
  },
  {
    key: 'detail',
    title: t('activity.detail'),
    minWidth: 180,
    hidden: true,
    ellipsis: { tooltip: true },
    render: (a) => a.detail || '—',
  },
])

const view = useTableView<Activity>({
  id: 'activities',
  columns: (): TableColumn<Activity>[] => columns.value,
  rows: (): Activity[] => list.rows.value,
  groupings,
})

const list = useList(activityApi.list, {
  live: ['request', 'issue', 'asset', 'license', 'consumable', 'order'],
  ordering: '-occurred_at',
  groupOrdering: view.groupOrdering,
  filters: { area: [], kind: [], actor: [], since: null, until: null },
})
onMounted(list.load)
</script>

<template>
  <div class="page">
    <PageHeader :title="t('activity.title')" :subtitle="t('activity.subtitle')" />
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
