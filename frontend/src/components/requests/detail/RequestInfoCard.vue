<script setup lang="ts">
import { NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import { useFormat } from '@/composables/useFormat'
import type { AssetRequest } from '@/types/requests'

/** Who asked for what and when: requester, period and the messages exchanged. */
const props = defineProps<{ assetRequest: AssetRequest }>()
const { t } = useI18n()
const { date, weekday, enumLabel } = useFormat()

const period = computed(() => {
  const r = props.assetRequest
  return r.duration === 'permanent'
    ? `${date(r.start_date)} → ${t('common.permanent')}`
    : `${date(r.start_date)} → ${date(r.end_date)}`
})

const entries = computed<DetailEntry[]>(() => {
  const r = props.assetRequest
  return [
    { label: t('requests.requester'), value: r.requester.display_name },
    { label: t('requests.department'), value: r.department?.name },
    // Recorded by someone else, e.g. IT on behalf of the employee.
    ...(r.created_by && r.created_by.id !== r.requester.id
      ? [{ label: t('requests.detail.createdBy'), value: r.created_by.display_name }]
      : []),
    ...(r.follows
      ? [
          {
            label: t('requests.again.follows'),
            value: `${r.follows.number} · ${enumLabel('requestStatus', r.follows.status)}`,
          },
        ]
      : []),
    ...(r.origin !== 'request'
      ? [
          {
            label: t('requests.detail.origin'),
            value: t(
              r.origin === 'quick' ? 'inventory.quickAssign.title' : 'requests.direct.title',
            ),
          },
        ]
      : []),
    { label: t('requests.duration'), value: enumLabel('duration', r.duration) },
    { label: t('requests.period'), value: period.value, slot: 'period' },
    ...(r.requested_pickup_date
      ? [
          {
            label: t('requests.requestedPickup'),
            value: weekday(r.requested_pickup_date),
            mono: true,
          },
        ]
      : []),
    { label: t('common.createdAt'), value: date(r.created_at), mono: true },
    ...(r.notes ? [{ label: t('requests.notes'), value: r.notes, wide: true }] : []),
    ...(r.it_comment
      ? [{ label: t('requests.itComment'), value: r.it_comment, wide: true }]
      : []),
  ]
})
</script>

<template>
  <NCard :title="t('requests.detail.request')" size="small">
    <DetailGrid :entries="entries">
      <template #period>
        <span class="mono">{{ period }}</span>
        <span v-if="assetRequest.is_overdue" class="overdue">
          · {{ t('requests.overdue') }}</span
        >
      </template>
    </DetailGrid>
  </NCard>
</template>

<style scoped>
.overdue {
  color: var(--ar-error);
  font-weight: 600;
}
</style>
