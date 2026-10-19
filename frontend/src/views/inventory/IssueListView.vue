<script setup lang="ts">
import { NButton, NDataTable, NInput, NModal, NSelect, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { teamsApi, usersApi } from '@/api/accounts'
import { issuesApi } from '@/api/inventory'
import AssignedTabs from '@/components/common/AssignedTabs.vue'
import AssignmentFields from '@/components/common/AssignmentFields.vue'
import { assignmentCell } from '@/components/common/assignmentCell'
import CheckField from '@/components/common/CheckField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useAction } from '@/composables/useAction'
import { useAssigned } from '@/composables/useAssigned'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import type { Team, User } from '@/types/accounts'
import type { Id } from '@/types/common'
import { ISSUE_KINDS, type AssetIssue, type IssueStatus } from '@/types/inventory'

/** Problems employees reported for their devices; IT takes them into work and resolves them. */
const { t } = useI18n()
const { date, dateTime, enumLabel } = useFormat()
const { busy, run } = useAction()

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

const selected = ref<AssetIssue | null>(null)
const resolution = ref('')
const showHandle = ref(false)

function open(issue: AssetIssue) {
  selected.value = issue
  resolution.value = issue.resolution
  showHandle.value = true
}

const assignSelected = (data: { team: Id | null; assignee: Id | null }) =>
  issuesApi.assign(selected.value!.id, data)

function onAssigned(issue: AssetIssue) {
  selected.value = issue
  list.load()
}

async function setStatus(status: IssueStatus) {
  if (!selected.value) return
  const updated = await run(
    () => issuesApi.update(selected.value!.id, { status, resolution: resolution.value }),
    t('common.saved'),
  )
  if (updated) {
    showHandle.value = false
    list.load()
  }
}

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
        :row-props="(i: AssetIssue) => ({ onClick: () => open(i) })"
        :scroll-x="1160"
        @update:sorter="list.onSort"
      />
    </div>

    <NModal
      v-model:show="showHandle"
      preset="card"
      :title="t('inventory.issues.handle')"
      style="max-width: 560px"
    >
      <div v-if="selected" class="handle">
        <div class="head">
          <StatusTag group="issueStatus" :value="selected.status" />
          <strong>{{ enumLabel('issueKind', selected.kind) }}</strong>
          <span class="muted small">
            {{ selected.asset.inventory_number }} · {{ selected.asset.model.full_name }}
          </span>
        </div>
        <p class="description">{{ selected.description }}</p>
        <p class="muted small">
          {{ selected.reported_by?.display_name }} · {{ dateTime(selected.created_at) }}
          <template v-if="selected.handled_by">
            · {{ t('inventory.issues.handledBy', { name: selected.handled_by.display_name }) }}
          </template>
        </p>
        <div class="field">
          <span class="eyebrow">{{ t('common.assignment.title') }}</span>
          <AssignmentFields
            :key="selected.id"
            :team="selected.assigned_team"
            :assignee="selected.assignee"
            :assign="assignSelected"
            @updated="onAssigned"
          />
        </div>
        <div class="field">
          <FieldLabel
            :label="t('inventory.issues.resolution')"
            :help="t('inventory.issues.resolutionHelp')"
          />
          <NInput
            v-model:value="resolution"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 6 }"
            :placeholder="t('inventory.issues.resolutionPlaceholder')"
          />
        </div>
      </div>
      <template #footer>
        <div v-if="selected" class="row" style="justify-content: flex-end">
          <NButton
            v-if="selected.status === 'resolved'"
            :loading="busy"
            @click="setStatus('open')"
            >{{ t('inventory.issues.reopen') }}</NButton
          >
          <NButton
            v-if="selected.status === 'open'"
            :loading="busy"
            @click="setStatus('in_progress')"
            >{{ t('inventory.issues.startWork') }}</NButton
          >
          <NButton
            type="primary"
            :loading="busy"
            :disabled="!resolution.trim()"
            @click="setStatus('resolved')"
            >{{ t('inventory.issues.resolve') }}</NButton
          >
        </div>
      </template>
    </NModal>
  </div>
</template>

<style scoped>
.handle {
  display: grid;
  gap: 10px;
}
.head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 10px;
}
.description {
  margin: 0;
  padding: 10px 12px;
  border-radius: 3px;
  background: var(--ar-surface-sunken);
  white-space: pre-wrap;
}
.field {
  display: grid;
  gap: 6px;
}
.small,
:deep(.small) {
  font-size: 12px;
}
</style>
