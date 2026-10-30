<script setup lang="ts">
import { NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'

/** The department's approval: who may decide, who did, and why. Only for requests that need it. */
const props = defineProps<{ assetRequest: Schemas['AssetRequestOut'] }>()
const { t } = useI18n()
const { dateTime } = useFormat()

const entries = computed<DetailEntry[]>(() => {
  const r = props.assetRequest
  if (r.approval === 'pending') {
    return [
      {
        label: t('requests.detail.waitingFor'),
        value: r.approvers.map((a) => a.display_name).join(', ') || null,
        wide: true,
      },
    ]
  }
  const self = r.approver?.id === r.requester.id
  return [
    {
      label: t('requests.detail.decidedBy'),
      value: r.approver
        ? `${r.approver.display_name}${self ? ` · ${t('requests.detail.selfApproved')}` : ''}`
        : null,
    },
    {
      label: t('requests.detail.decidedAt'),
      value: r.approval_decided_at ? dateTime(r.approval_decided_at) : null,
      mono: true,
    },
    ...(r.approval_comment
      ? [{ label: t('requests.approval.comment'), value: r.approval_comment, wide: true }]
      : []),
  ]
})
</script>

<template>
  <NCard :title="t('requests.detail.approval')" size="small">
    <template #header-extra>
      <StatusTag group="approval" :value="assetRequest.approval" />
    </template>
    <DetailGrid :entries="entries" />
  </NCard>
</template>
