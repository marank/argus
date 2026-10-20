<script setup lang="ts">
import { NDataTable, NInput, NSelect, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRouter } from 'vue-router'

import { teamsApi, usersApi } from '@/api/accounts'
import { issuesApi } from '@/api/inventory'
import AssignedTabs from '@/components/common/AssignedTabs.vue'
import { assignmentCell } from '@/components/common/assignmentCell'
import CheckField from '@/components/common/CheckField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useAssigned } from '@/composables/useAssigned'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import type { Team, User } from '@/types/accounts'
import { ISSUE_KINDS, type AssetIssue, type IssueStatus } from '@/types/inventory'

/** Problems employees reported for their devices; each opens its page with the conversation. */
const { t } = useI18n()
const router = useRouter()
const { date, enumLabel } = useFormat()

const OPEN: IssueStatus[] = ['open', 'in_progress']
const { assigned, param: assignedParam } = useAssigned('issues')
const list = useList(issuesApi.list, {
  ordering: '-created_at',
  filters: {
    status: [...OPEN],
    kind: null,
    assigned: assignedParam(assigned.value),
    team: [],
    assignee: null,
  },
})
onMounted(list.load)
watch(assigned, (value) => (list.filters.assigned = assignedParam(value)))

const onlyOpen = computed({
  get: () => (list.filters.status as string[]).length > 0,
  set: (value: boolean) => (list.filters.status = value ? [...OPEN] : []),
})
const kindOptions = computed(() =>
  ISSUE_KINDS.map((k) => ({ value: k, label: enumLabel('issueKind', k) })),
)

const columns = computed<DataTableColumns<AssetIssue>>(() => [
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
])
</script>

<template>
  <div class="page">
    <PageHeader :title="t('inventory.issues.title')" :subtitle="t('inventory.issues.subtitle')" />
    <div class="stack">
      <div class="toolbar">
        <AssignedTabs v-model="assigned" />
        <NInput
          v-model:value="list.search.value"
          class="grow"
          :placeholder="t('common.search')"
          clearable
        />
        <NSelect
          v-model:value="list.filters.kind as string | null"
          :options="kindOptions"
          :placeholder="t('inventory.issues.kind')"
          clearable
          style="width: 200px"
        />
        <EntitySelect
          v-model="list.filters.team as string[]"
          :fetcher="teamsApi.list"
          :label="(team: Team) => team.name"
          multiple
          max-tag-count="responsive"
          :placeholder="t('common.assignment.team')"
          style="width: 180px"
        />
        <EntitySelect
          v-model="list.filters.assignee as string | null"
          :fetcher="usersApi.list"
          :params="{ is_staff: true }"
          :label="(user: User) => user.display_name"
          :placeholder="t('common.assignment.assignee')"
          style="width: 180px"
        />
        <CheckField v-model="onlyOpen" :label="t('inventory.issues.onlyOpen')" />
      </div>
      <NDataTable
        class="clickable-rows"
        remote
        size="small"
        :columns="columns"
        :data="list.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(i: AssetIssue) => i.id"
        :row-props="
          (i: AssetIssue) => ({
            onClick: () => router.push({ name: 'issue', params: { id: i.id } }),
          })
        "
        :scroll-x="1160"
        @update:sorter="list.onSort"
      />
    </div>
  </div>
</template>

<style scoped>
.small,
:deep(.small) {
  font-size: 12px;
}
</style>
