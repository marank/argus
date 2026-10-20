<script setup lang="ts">
import { CircleCheck, CircleDot } from '@lucide/vue'
import { NDataTable, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { portalApi } from '@/api/reservations'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import { useGroupedRows, withGroupHeaders } from '@/composables/useGroupedRows'
import { useLive } from '@/composables/useLive'
import type { OwnIssueWithDevice } from '@/types/inventory'
import { categoryIcon } from '@/utils/icons'

/** All problems the employee reported, open ones first; each opens its conversation. */
const { t } = useI18n()
const router = useRouter()
const { date, enumLabel } = useFormat()

/** Reports IT changed since the employee last opened them pulse until opened. */
const issues = ref<OwnIssueWithDevice[] | null>(null)
const load = async () => (issues.value = await portalApi.myIssues())
onMounted(load)
useLive(['issue'], load)

const isDone = (i: OwnIssueWithDevice) => i.status === 'resolved'
/** Open and in-progress reports first; newest first within each section (as delivered). */
const sorted = computed(() => {
  const all = issues.value ?? []
  return [...all.filter((i) => !isDone(i)), ...all.filter(isDone)]
})

const grouping = useGroupedRows<OwnIssueWithDevice>({
  rows: () => sorted.value,
  key: (i) => (isDone(i) ? 'done' : 'current'),
  label: (i) => [
    h(isDone(i) ? CircleCheck : CircleDot, { size: 14 }),
    t(isDone(i) ? 'reservations.myIssues.done' : 'reservations.myIssues.current'),
  ],
  storageKey: 'argus.groups.my-issues',
})

function openIssue(issue: OwnIssueWithDevice) {
  router.push({ name: 'portal-issue', params: { id: issue.id } })
}

const columns = computed(() =>
  withGroupHeaders<OwnIssueWithDevice>([
    {
      key: 'device',
      title: t('reservations.myDevices.device'),
      minWidth: 230,
      render: (i) =>
        h('div', { class: 'device-cell' }, [
          h(categoryIcon(i.asset.category_icon), { size: 16, class: 'muted' }),
          h('div', [
            h('div', i.asset.model.full_name),
            h('small', { class: 'muted mono' }, [
              i.asset.inventory_number,
              i.still_assigned ? null : ` · ${t('reservations.myIssues.returned')}`,
            ]),
          ]),
        ]),
    },
    {
      key: 'status',
      title: t('common.status'),
      width: 150,
      render: (i) =>
        h(StatusTag, { group: 'issueStatus', value: i.status, pulse: i.unseen_update }),
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
      minWidth: 220,
      ellipsis: { tooltip: true },
    },
    {
      key: 'last_message',
      title: t('inventory.issues.lastMessage'),
      minWidth: 220,
      ellipsis: { tooltip: true },
      render: (i) => i.last_message || h('span', { class: 'muted' }, '—'),
    },
    {
      key: 'created_at',
      title: t('inventory.issues.reportedAt'),
      width: 120,
      render: (i) => h('span', { class: 'mono' }, date(i.created_at)),
    },
  ] as DataTableColumns<OwnIssueWithDevice>),
)
</script>

<template>
  <div class="page">
    <PageHeader
      :title="t('reservations.myIssues.title')"
      :subtitle="t('reservations.myIssues.subtitle')"
    />
    <EmptyState v-if="issues && !issues.length" :text="t('reservations.myIssues.empty')" />
    <NDataTable
      v-else
      class="clickable-rows"
      size="small"
      :columns="columns"
      :data="grouping.rows.value"
      :loading="!issues"
      :row-key="(i: OwnIssueWithDevice) => i.id"
      :row-props="(i: OwnIssueWithDevice) => grouping.rowProps(i, openIssue)"
      :row-class-name="grouping.rowClass"
      :scroll-x="1100"
    />
  </div>
</template>

<style scoped>
:deep(.device-cell) {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
