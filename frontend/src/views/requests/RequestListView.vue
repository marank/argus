<script setup lang="ts">
import { HandHelping, Plus } from '@lucide/vue'
import { NButton, NRadioButton, NRadioGroup } from 'naive-ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { departmentsApi, teamsApi, usersApi } from '@/api/accounts'
import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import AssignedTabs from '@/components/common/AssignedTabs.vue'
import { assignmentCell } from '@/components/common/assignmentCell'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ListTable from '@/components/table/ListTable.vue'
import TableToolbar from '@/components/table/TableToolbar.vue'
import type { TableColumn, TableFilter, TableGrouping } from '@/components/table/types'
import { useFormat } from '@/composables/useFormat'
import { useAssigned } from '@/composables/useAssigned'
import { useList } from '@/composables/useList'
import { useTableView } from '@/composables/useTableView'
import { useAuthStore } from '@/stores/auth'
import { ASSET_REQUEST_STATUSES } from '@/types/requests'
import { isPast } from '@/utils/requests'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { date, weekday, enumLabel } = useFormat()
const canWrite = computed(() => useAuthStore().can('requests', 'write'))

type AssetRequest = Schemas['AssetRequestListOut']

type Scope = 'open' | 'overdue' | 'all'
const scope = ref<Scope>(route.query.overdue ? 'overdue' : route.query.status ? 'all' : 'open')

const { assigned, param: assignedParam } = useAssigned('requests')

watch(scope, (value) => {
  list.filters.open = value === 'open' ? true : null
  list.filters.overdue = value === 'overdue' ? true : null
})

watch(assigned, (value) => (list.filters.assigned = assignedParam(value)))

/** Before the handout the employee's preferred pickup day still matters. */
const WISH_STATUSES = new Set<Schemas['AssetRequestStatus']>([
  'pending_approval',
  'submitted',
  'confirmed',
  'ready',
])

const durationLabel = (d: string) => t(`enums.duration.${d}`)

const filters = computed<TableFilter[]>(() => [
  {
    key: 'status',
    label: t('common.status'),
    type: 'select',
    options: ASSET_REQUEST_STATUSES.map((s) => ({
      value: s,
      label: enumLabel('requestStatus', s),
    })),
  },
  {
    key: 'duration',
    label: t('requests.duration'),
    type: 'select',
    options: ['temporary', 'permanent'].map((d) => ({ value: d, label: durationLabel(d) })),
  },
  {
    key: 'requester',
    label: t('requests.requester'),
    type: 'entity',
    fetcher: usersApi.list,
    display: (user: Schemas['UserOut']) => user.display_name,
  },
  {
    key: 'department',
    label: t('requests.department'),
    type: 'entity',
    fetcher: departmentsApi.list,
    display: (d: Schemas['DepartmentOut']) => d.path.join(' / '),
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
    key: 'start_date',
    label: t('requests.startDate'),
    type: 'daterange',
    from: 'start_from',
    until: 'start_until',
  },
])

const groupings = (): TableGrouping<AssetRequest>[] => [
  {
    key: 'status',
    label: t('common.status'),
    ordering: 'status',
    rowKey: (r) => r.status,
    rowLabel: (r) => h(StatusTag, { group: 'requestStatus', value: r.status }),
  },
  {
    key: 'duration',
    label: t('requests.duration'),
    ordering: 'duration',
    rowKey: (r) => r.duration,
    rowLabel: (r) => durationLabel(r.duration),
  },
  {
    key: 'department',
    label: t('requests.department'),
    ordering: 'requester__department__name,requester__department_id',
    rowKey: (r) => r.department?.id ?? '',
    rowLabel: (r) =>
      r.department?.name ??
      h('span', { class: 'muted' }, t('table.without', { name: t('requests.department') })),
  },
  {
    key: 'team',
    label: t('common.assignment.team'),
    ordering: 'assigned_team__name,assigned_team_id',
    rowKey: (r) => r.assigned_team?.id ?? '',
    rowLabel: (r) =>
      r.assigned_team?.name ?? h('span', { class: 'muted' }, t('common.assignment.noTeam')),
  },
]

const columns = computed<TableColumn<AssetRequest>[]>(() => [
  {
    key: 'number',
    title: t('requests.number'),
    sorter: true,
    hideable: false,
    width: 135,
    render: (r) => h('span', { class: 'mono strong' }, r.number),
  },
  {
    key: 'status',
    title: t('common.status'),
    sorter: true,
    width: 125,
    // Right after the number: it decides what to do next. Pulse: new requests wait for confirmation.
    render: (r) =>
      h(StatusTag, {
        group: 'requestStatus',
        value: r.status,
        pulse: r.status === 'submitted',
      }),
  },
  {
    key: 'title',
    title: t('requests.purpose'),
    minWidth: 200,
    render: (r) =>
      h('div', [
        h('div', [
          r.title,
          r.origin === 'direct' ? h('span', { class: 'origin' }, t('requests.direct.badge')) : null,
        ]),
        h('small', { class: 'muted' }, r.summary),
      ]),
  },
  {
    key: 'requester',
    title: t('requests.requester'),
    width: 160,
    render: (r) =>
      h('div', [
        h('div', r.requester.display_name),
        h('small', { class: 'muted' }, r.department?.name ?? ''),
      ]),
  },
  {
    key: 'assignment',
    title: t('common.assignment.title'),
    width: 150,
    render: assignmentCell,
  },
  {
    key: 'start_date',
    title: t('requests.period'),
    sorter: true,
    width: 190,
    render: (r) =>
      h(
        'span',
        { class: ['mono', r.is_overdue ? 'overdue' : ''] },
        `${date(r.start_date)} → ${r.end_date ? date(r.end_date) : '∞'}`,
      ),
  },
  {
    key: 'pickup_at',
    title: t('requests.pickupAt'),
    sorter: true,
    width: 160,
    render: (r) => {
      if (r.pickup_at) return h('span', { class: 'mono nowrap' }, weekday(r.pickup_at))
      // No appointment yet: the employee's preferred day, marked as a wish in a quiet second line.
      if (r.requested_pickup_date && WISH_STATUSES.has(r.status)) {
        const wish = t('requests.wishLabel')
        return h('div', [
          h('div', { class: 'mono nowrap' }, weekday(r.requested_pickup_date)),
          h(
            'small',
            { class: 'muted wish nowrap' },
            isPast(r.requested_pickup_date) ? `${wish} · ${t('requests.datePassed')}` : wish,
          ),
        ])
      }
      return h('span', { class: 'mono' }, '—')
    },
  },
  // Further columns to show from the column settings.
  {
    key: 'department',
    title: t('requests.department'),
    hidden: true,
    width: 160,
    render: (r) => r.department?.name ?? '—',
  },
  {
    key: 'duration',
    title: t('requests.duration'),
    hidden: true,
    width: 120,
    render: (r) => enumLabel('duration', r.duration),
  },
  {
    key: 'end_date',
    title: t('requests.endDate'),
    sorter: true,
    hidden: true,
    width: 120,
    render: (r) => h('span', { class: 'mono' }, r.end_date ? date(r.end_date) : '∞'),
  },
  {
    key: 'handover_mode',
    title: t('handover.method'),
    hidden: true,
    width: 190,
    render: (r) => t(`handover.mode.${r.handover_mode}`),
  },
  {
    key: 'approval',
    title: t('requests.approval.label'),
    hidden: true,
    width: 130,
    render: (r) => enumLabel('approval', r.approval),
  },
  {
    key: 'item_count',
    title: t('requests.itemCount'),
    hidden: true,
    width: 100,
    align: 'right',
    render: (r) => h('span', { class: 'mono' }, r.item_count),
  },
  {
    key: 'unit_count',
    title: t('requests.unitCount'),
    hidden: true,
    width: 90,
    align: 'right',
    render: (r) => h('span', { class: 'mono' }, r.unit_count),
  },
  {
    key: 'created_at',
    title: t('common.createdAt'),
    sorter: true,
    hidden: true,
    width: 120,
    render: (r) => h('span', { class: 'mono' }, date(r.created_at)),
  },
])

const view = useTableView<AssetRequest>({
  id: 'requests',
  columns: (): TableColumn<AssetRequest>[] => columns.value,
  rows: (): AssetRequest[] => list.rows.value,
  groupings,
})

const list = useList(requestsApi.list, {
  live: ['request'],
  ordering: 'start_date',
  groupOrdering: view.groupOrdering,
  filters: {
    status: route.query.status ? [String(route.query.status)] : [],
    department: [],
    requester: [],
    start_from: null,
    start_until: null,
    duration: [],
    open: scope.value === 'open' ? true : null,
    overdue: scope.value === 'overdue' ? true : null,
    assigned: assignedParam(assigned.value),
    team: [],
    assignee: [],
  },
})
onMounted(list.load)
</script>

<template>
  <div class="page">
    <PageHeader :title="t('requests.title')" :subtitle="t('requests.subtitle')">
      <template #actions>
        <RouterLink v-if="canWrite" :to="{ name: 'direct-handout' }">
          <NButton>
            <template #icon><HandHelping :size="16" /></template>
            {{ t('requests.direct.action') }}
          </NButton>
        </RouterLink>
        <RouterLink :to="{ name: 'portal-new' }">
          <NButton type="primary">
            <template #icon><Plus :size="16" /></template>
            {{ t('nav.newRequest') }}
          </NButton>
        </RouterLink>
      </template>
    </PageHeader>
    <div class="stack">
      <TableToolbar v-model:search="list.search.value" :list="list" :filters="filters" :view="view">
        <template #prefix>
          <NRadioGroup v-model:value="scope" size="small">
            <NRadioButton value="open">{{ t('requests.onlyOpen') }}</NRadioButton>
            <NRadioButton value="overdue">{{ t('requests.onlyOverdue') }}</NRadioButton>
            <NRadioButton value="all">{{ t('common.all') }}</NRadioButton>
          </NRadioGroup>
          <AssignedTabs v-model="assigned" />
        </template>
      </TableToolbar>
      <ListTable
        :view="view"
        :list="list"
        @row-click="(r: AssetRequest) => router.push({ name: 'request', params: { id: r.id } })"
      />
    </div>
  </div>
</template>

<style scoped>
:deep(.strong) {
  font-weight: 600;
}
:deep(.origin) {
  margin-left: 6px;
  padding: 0 5px;
  border: 1px solid var(--ar-border);
  border-radius: 2px;
  color: var(--ar-text-muted);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
:deep(.overdue) {
  color: var(--ar-error);
  font-weight: 600;
}
</style>
