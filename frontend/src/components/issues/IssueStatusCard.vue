<script setup lang="ts">
import { NButton, NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import AssignmentFields from '@/components/common/AssignmentFields.vue'
import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import { type AssignFn, useAssignment } from '@/composables/useAssignment'
import { useFormat } from '@/composables/useFormat'

/**
 * Where the report stands: kind, who reported it and when, who handles it. IT
 * with write rights changes the assignment right here (`assign`) and saves it with the
 * button next to it.
 */
const props = defineProps<{
  issue: Schemas['AssetIssueDetailOut']
  assign?: AssignFn<Schemas['AssetIssueDetailOut']>
}>()
const emit = defineEmits<{ updated: [issue: Schemas['AssetIssueDetailOut']] }>()
const { t } = useI18n()
const { dateTime, enumLabel } = useFormat()

const form = useAssignment(
  () => ({ team: props.issue.assigned_team, assignee: props.issue.assignee }),
  (data) => props.assign!(data),
  (issue) => emit('updated', issue),
)

const entries = computed<DetailEntry[]>(() => {
  const i = props.issue
  return [
    { label: t('inventory.issues.kind'), value: enumLabel('issueKind', i.kind) },
    { label: t('inventory.issues.reportedBy'), value: i.reported_by?.display_name },
    { label: t('inventory.issues.reportedAt'), value: dateTime(i.created_at), mono: true },
    ...(i.handled_by
      ? [{ label: t('inventory.issues.detail.handledBy'), value: i.handled_by.display_name }]
      : []),
    ...(i.resolved_at
      ? [
          {
            label: t('inventory.issues.detail.resolvedAt'),
            value: dateTime(i.resolved_at),
            mono: true,
          },
        ]
      : []),
    // Without the right to change it, the assignment is just shown.
    ...(!props.assign && (i.assigned_team || i.assignee)
      ? [
          {
            label: t('common.assignment.title'),
            value: [i.assigned_team?.name, i.assignee?.display_name].filter(Boolean).join(' · '),
          },
        ]
      : []),
  ]
})
</script>

<template>
  <NCard :title="t('inventory.issues.detail.report')" size="small">
    <div class="stack">
      <DetailGrid :entries="entries" />
      <div v-if="assign" class="field">
        <div class="field-head">
          <span class="eyebrow">{{ t('common.assignment.title') }}</span>
          <NButton
            size="small"
            type="primary"
            :disabled="!form.dirty"
            :loading="form.busy"
            @click="form.save"
          >
            {{ t('common.save') }}
          </NButton>
        </div>
        <AssignmentFields
          :key="issue.id"
          :team="issue.assigned_team"
          :assignee="issue.assignee"
          :form="form"
        />
      </div>
    </div>
  </NCard>
</template>

<style scoped>
.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.field-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
}
</style>
