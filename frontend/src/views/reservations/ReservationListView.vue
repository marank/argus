<script setup lang="ts">
import { Plus } from '@lucide/vue'
import {
  NButton,
  NDataTable,
  NInput,
  NRadioButton,
  NRadioGroup,
  NSelect,
  NTag,
  type DataTableColumns,
} from 'naive-ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { departmentsApi, teamsApi, usersApi } from '@/api/accounts'
import { reservationsApi } from '@/api/reservations'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import type { Team, User } from '@/types/accounts'
import { RESERVATION_STATUSES, type ReservationListItem } from '@/types/reservations'

const { t } = useI18n()
const route = useRoute()
const router = useRouter()
const { date, weekday, enumLabel } = useFormat()

type Scope = 'open' | 'overdue' | 'all'
const scope = ref<Scope>(route.query.overdue ? 'overdue' : route.query.status ? 'all' : 'open')

/** Whose requests: remembered per browser, since each IT member mostly wants the same view. */
type Assigned = 'me' | 'my_teams' | 'nobody' | 'all'
const ASSIGNED_KEY = 'argus.reservations.assigned'
function storedAssigned(): Assigned {
  try {
    const value = localStorage.getItem(ASSIGNED_KEY)
    return value === 'me' || value === 'my_teams' || value === 'nobody' ? value : 'all'
  } catch {
    return 'all'
  }
}
const assigned = ref<Assigned>(storedAssigned())

const list = useList(reservationsApi.list, {
  ordering: 'start_date',
  filters: {
    status: route.query.status ? [String(route.query.status)] : [],
    department: null,
    duration: null,
    open: scope.value === 'open' ? true : null,
    overdue: scope.value === 'overdue' ? true : null,
    assigned: assigned.value === 'all' ? null : assigned.value,
    team: [],
    assignee: null,
  },
})
onMounted(list.load)

watch(scope, (value) => {
  list.filters.open = value === 'open' ? true : null
  list.filters.overdue = value === 'overdue' ? true : null
})

watch(assigned, (value) => {
  list.filters.assigned = value === 'all' ? null : value
  try {
    localStorage.setItem(ASSIGNED_KEY, value)
  } catch {
    // Private mode or blocked storage: the choice just is not remembered.
  }
})

const statusOptions = computed(() =>
  RESERVATION_STATUSES.map((s) => ({ value: s, label: enumLabel('reservationStatus', s) })),
)

const columns = computed<DataTableColumns<ReservationListItem>>(() => [
  {
    key: 'number',
    title: t('reservations.number'),
    sorter: true,
    width: 140,
    render: (r) => h('span', { class: 'mono strong' }, r.number),
  },
  {
    key: 'title',
    title: t('reservations.purpose'),
    minWidth: 220,
    render: (r) => h('div', [h('div', r.title), h('small', { class: 'muted' }, r.summary)]),
  },
  {
    key: 'requester',
    title: t('reservations.requester'),
    width: 180,
    render: (r) =>
      h('div', [
        h('div', r.requester.display_name),
        h('small', { class: 'muted' }, r.department?.name ?? ''),
      ]),
  },
  {
    key: 'assignment',
    title: t('reservations.assignment.title'),
    width: 170,
    render: (r) =>
      r.assigned_team || r.assignee
        ? h('div', [
            r.assigned_team
              ? h(NTag, { size: 'small', bordered: false }, () => r.assigned_team!.name)
              : null,
            r.assignee ? h('small', { class: 'assignee' }, r.assignee.display_name) : null,
          ])
        : h('span', { class: 'muted' }, '—'),
  },
  {
    key: 'start_date',
    title: t('reservations.period'),
    sorter: true,
    width: 220,
    render: (r) =>
      h(
        'span',
        { class: ['mono', r.is_overdue ? 'overdue' : ''] },
        `${date(r.start_date)} → ${r.end_date ? date(r.end_date) : '∞'}`,
      ),
  },
  {
    key: 'unit_count',
    title: t('common.quantity'),
    width: 70,
    align: 'right',
    render: (r) => h('span', { class: 'mono' }, r.unit_count),
  },
  {
    key: 'pickup_at',
    title: t('reservations.pickupAt'),
    sorter: true,
    width: 180,
    render: (r) => h('span', { class: 'mono nowrap' }, r.pickup_at ? weekday(r.pickup_at) : '—'),
  },
  {
    key: 'status',
    title: t('common.status'),
    sorter: true,
    width: 150,
    // Pulse: new requests wait for approval.
    render: (r) =>
      h(StatusTag, {
        group: 'reservationStatus',
        value: r.status,
        pulse: r.status === 'submitted',
      }),
  },
])
</script>

<template>
  <div class="page">
    <PageHeader :title="t('reservations.title')" :subtitle="t('reservations.subtitle')">
      <template #actions>
        <RouterLink :to="{ name: 'portal-new' }">
          <NButton type="primary">
            <template #icon><Plus :size="16" /></template>
            {{ t('nav.newRequest') }}
          </NButton>
        </RouterLink>
      </template>
    </PageHeader>
    <div class="stack">
      <div class="toolbar">
        <NRadioGroup v-model:value="scope" size="small">
          <NRadioButton value="open">{{ t('reservations.onlyOpen') }}</NRadioButton>
          <NRadioButton value="overdue">{{ t('reservations.onlyOverdue') }}</NRadioButton>
          <NRadioButton value="all">{{ t('common.all') }}</NRadioButton>
        </NRadioGroup>
        <NRadioGroup v-model:value="assigned" size="small">
          <NRadioButton value="me">{{ t('reservations.assignment.me') }}</NRadioButton>
          <NRadioButton value="my_teams">{{ t('reservations.assignment.myTeams') }}</NRadioButton>
          <NRadioButton value="nobody">{{ t('reservations.assignment.unassigned') }}</NRadioButton>
          <NRadioButton value="all">{{ t('reservations.assignment.allAssignments') }}</NRadioButton>
        </NRadioGroup>
        <NInput
          v-model:value="list.search.value"
          class="grow"
          :placeholder="t('common.search')"
          clearable
        />
        <NSelect
          v-model:value="list.filters.status as string[]"
          :options="statusOptions"
          multiple
          clearable
          max-tag-count="responsive"
          :placeholder="t('common.status')"
          style="width: 220px"
        />
        <NSelect
          v-model:value="list.filters.duration as string | null"
          :options="[
            { value: 'temporary', label: t('enums.duration.temporary') },
            { value: 'permanent', label: t('enums.duration.permanent') },
          ]"
          clearable
          :placeholder="t('reservations.duration')"
          style="width: 150px"
        />
        <EntitySelect
          v-model="list.filters.department as string | null"
          :fetcher="departmentsApi.list"
          :label="(d) => d.name"
          :placeholder="t('reservations.department')"
          style="width: 180px"
        />
        <EntitySelect
          v-model="list.filters.team as string[]"
          :fetcher="teamsApi.list"
          :label="(team: Team) => team.name"
          multiple
          max-tag-count="responsive"
          :placeholder="t('reservations.assignment.team')"
          style="width: 180px"
        />
        <EntitySelect
          v-model="list.filters.assignee as string | null"
          :fetcher="usersApi.list"
          :params="{ is_staff: true }"
          :label="(user: User) => user.display_name"
          :placeholder="t('reservations.assignment.assignee')"
          style="width: 180px"
        />
      </div>
      <NDataTable
        class="clickable-rows"
        remote
        size="small"
        :columns="columns"
        :data="list.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(r: ReservationListItem) => r.id"
        :row-props="
          (r: ReservationListItem) => ({
            onClick: () => router.push({ name: 'reservation', params: { id: r.id } }),
          })
        "
        :scroll-x="1270"
        @update:sorter="list.onSort"
      />
    </div>
  </div>
</template>

<style scoped>
:deep(.strong) {
  font-weight: 600;
}
:deep(.assignee) {
  display: block;
  margin-top: 2px;
}
:deep(.overdue) {
  color: var(--ar-error);
  font-weight: 600;
}
</style>
