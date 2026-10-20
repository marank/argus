<script setup lang="ts">
import { NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import type { Reservation } from '@/types/reservations'

/** The department's approval: who may decide, who did, and why. Only for requests that need it. */
const props = defineProps<{ reservation: Reservation }>()
const { t } = useI18n()
const { dateTime } = useFormat()

const entries = computed<DetailEntry[]>(() => {
  const r = props.reservation
  if (r.approval === 'pending') {
    return [
      {
        label: t('reservations.detail.waitingFor'),
        value: r.approvers.map((a) => a.display_name).join(', ') || null,
        wide: true,
      },
    ]
  }
  const self = r.approver?.id === r.requester.id
  return [
    {
      label: t('reservations.detail.decidedBy'),
      value: r.approver
        ? `${r.approver.display_name}${self ? ` · ${t('reservations.detail.selfApproved')}` : ''}`
        : null,
    },
    {
      label: t('reservations.detail.decidedAt'),
      value: r.approval_decided_at ? dateTime(r.approval_decided_at) : null,
      mono: true,
    },
    ...(r.approval_comment
      ? [{ label: t('reservations.approval.comment'), value: r.approval_comment, wide: true }]
      : []),
  ]
})
</script>

<template>
  <NCard :title="t('reservations.detail.approval')" size="small">
    <template #header-extra>
      <StatusTag group="approval" :value="reservation.approval" />
    </template>
    <DetailGrid :entries="entries" />
  </NCard>
</template>
