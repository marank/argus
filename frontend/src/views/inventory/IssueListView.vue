<script setup lang="ts">
import { computed, h, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'

import { teamsApi, usersApi } from '@/api/accounts'
import { assetsApi, issuesApi } from '@/api/inventory'
import type { Schemas } from '@/api/types'
import AssignedTabs from '@/components/common/AssignedTabs.vue'
import { assignmentCell } from '@/components/common/assignmentCell'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ListTable from '@/components/table/ListTable.vue'
import TableToolbar from '@/components/table/TableToolbar.vue'
import type { TableColumn, TableFilter, TableGrouping } from '@/components/table/types'
import { useAssigned } from '@/composables/useAssigned'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { useTableView } from '@/composables/useTableView'
import { ISSUE_KINDS, ISSUE_STATUSES } from '@/types/inventory'

/** Problems employees reported for their devices; each opens its page with the conversation. */
type Issue = Schemas['AssetIssueOut']

const { t } = useI18n()
const router = useRouter()
const { date, enumLabel } = useFormat()

const OPEN: Schemas['AssetIssueStatus'][] = ['open', 'in_progress']
const { assigned, param: assignedParam } = useAssigned('issues')

const filters = computed<TableFilter[]>(() => [
  {
    key: 'asset',
    label: t('inventory.issues.device'),
    type: 'entity',
    fetcher: assetsApi.list,
    display: (a: Schemas['AssetOut']) => `${a.inventory_number} · ${a.model.full_name}`,
  },
  {
    key: 'status',
    label: t('common.status'),
    type: 'select',
    options: ISSUE_STATUSES.map((s) => ({ value: s, label: enumLabel('issueStatus', s) })),
  },
  {
    key: 'kind',
    label: t('inventory.issues.kind'),
    type: 'select',
    options: ISSUE_KINDS.map((k) => ({ value: k, label: enumLabel('issueKind', k) })),
  },
  {
    key: 'team',
    label: t('common.assignment.team'),
    type: 'entity',
    fetcher: teamsApi.list,
    display: (team: Schemas['TeamOut']) => team.name,
  },
  {
    key: 'assignee',
    label: t('common.assignment.assignee'),
    type: 'entity',
    fetcher: usersApi.list,
    params: { is_staff: true },
    display: (user: Schemas['UserOut']) => user.display_name,
  },
  {
    key: 'reported',
    label: t('inventory.issues.reportedAt'),
    type: 'daterange',
    from: 'reported_from',
    until: 'reported_until',
  },
])

const groupings = (): TableGrouping<Issue>[] => [
  {
    key: 'status',
    label: t('common.status'),
    ordering: 'status',
    rowKey: (i) => i.status,
    rowLabel: (i) => h(StatusTag, { group: 'issueStatus', value: i.status }),
  },
  {
    key: 'kind',
    label: t('inventory.issues.kind'),
    ordering: 'kind',
    rowKey: (i) => i.kind,
    rowLabel: (i) => enumLabel('issueKind', i.kind),
  },
  {
    key: 'team',
    label: t('common.assignment.team'),
    ordering: 'assigned_team__name,assigned_team_id',
    rowKey: (i) => i.assigned_team?.id ?? '',
    rowLabel: (i) =>
      i.assigned_team?.name ?? h('span', { class: 'muted' }, t('common.assignment.noTeam')),
  },
]

const columns = computed<TableColumn<Issue>[]>(() => [
  {
    key: 'status',
    title: t('common.status'),
    sorter: true,
    width: 150,
    // New reports wait for IT: the dot pulses.
    render: (i) =>
      h(StatusTag, { group: 'issueStatus', value: i.status, pulse: i.status === 'open' }),
  },
  {
    key: 'asset__inventory_number',
    title: t('inventory.issues.device'),
    sorter: true,
    minWidth: 230,
    render: (i) =>
      h('div', [
        h(
          RouterLink,
          {
            to: { name: 'asset', params: { id: i.asset.id } },
            class: 'mono',
            onClick: (e: Event) => e.stopPropagation(),
          },
          () => i.asset.inventory_number,
        ),
        h('div', { class: 'muted small' }, i.asset.model.full_name),
      ]),
  },
  {
    key: 'kind',
    title: t('inventory.issues.kind'),
    sorter: true,
    width: 170,
    render: (i) => enumLabel('issueKind', i.kind),
  },
  {
    key: 'description',
    title: t('common.description'),
    minWidth: 260,
    ellipsis: { tooltip: true },
  },
  {
    key: 'assignment',
    title: t('common.assignment.title'),
    width: 160,
    render: assignmentCell,
  },
  {
    key: 'reported_by',
    title: t('inventory.issues.reportedBy'),
    width: 160,
    render: (i) => i.reported_by?.display_name ?? '—',
  },
  {
    key: 'created_at',
    title: t('inventory.issues.reportedAt'),
    sorter: true,
    width: 120,
    render: (i) => h('span', { class: 'mono' }, date(i.created_at)),
  },
  // Further columns to show from the column settings.
  {
    key: 'model',
    title: t('inventory.fields.model'),
    hidden: true,
    width: 200,
    ellipsis: { tooltip: true },
    render: (i) => i.asset.model.full_name,
  },
  {
    key: 'device_user',
    title: t('inventory.fields.assignedTo'),
    hidden: true,
    width: 160,
    render: (i) => i.asset.assigned_to?.display_name ?? '—',
  },
  {
    key: 'handled_by',
    title: t('inventory.issues.detail.handledBy'),
    hidden: true,
    width: 160,
    render: (i) => i.handled_by?.display_name ?? '—',
  },
  {
    key: 'resolved_at',
    title: t('inventory.issues.detail.resolvedAt'),
    hidden: true,
    width: 120,
    render: (i) => h('span', { class: 'mono' }, date(i.resolved_at)),
  },
])

const view = useTableView<Issue>({
  id: 'issues',
  columns: (): TableColumn<Issue>[] => columns.value,
  rows: (): Issue[] => list.rows.value,
  groupings,
})

const list = useList(issuesApi.list, {
  live: ['issue'],
  ordering: '-created_at',
  groupOrdering: view.groupOrdering,
  filters: {
    status: [...OPEN],
    asset: [],
    kind: [],
    assigned: assignedParam(assigned.value),
    team: [],
    assignee: [],
    reported_from: null,
    reported_until: null,
  },
})
onMounted(list.load)
watch(assigned, (value) => (list.filters.assigned = assignedParam(value)))

const openIssue = (i: Issue) => router.push({ name: 'issue', params: { id: i.id } })
</script>

<template>
  <div class="page">
    <PageHeader :title="t('inventory.issues.title')" :subtitle="t('inventory.issues.subtitle')" />
    <div class="stack">
      <TableToolbar v-model:search="list.search.value" :list="list" :filters="filters" :view="view">
        <template #prefix><AssignedTabs v-model="assigned" /></template>
      </TableToolbar>
      <ListTable :view="view" :list="list" @row-click="openIssue" />
    </div>
  </div>
</template>

<style scoped>
.small,
:deep(.small) {
  font-size: 12px;
}
</style>
