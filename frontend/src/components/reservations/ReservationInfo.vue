<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import { useFormat } from '@/composables/useFormat'
import type { Reservation } from '@/types/reservations'

const props = defineProps<{ reservation: Reservation }>()
const { t } = useI18n()
const { date, weekday, enumLabel } = useFormat()

const period = computed(() => {
  const r = props.reservation
  return r.duration === 'permanent'
    ? `${date(r.start_date)} → ${t('common.permanent')}`
    : `${date(r.start_date)} → ${date(r.end_date)}`
})

const entries = computed<DetailEntry[]>(() => {
  const r = props.reservation
  return [
    { label: t('reservations.requester'), value: r.requester.display_name },
    { label: t('reservations.department'), value: r.department?.name },
    { label: t('reservations.duration'), value: enumLabel('duration', r.duration) },
    { label: t('reservations.period'), value: period.value, mono: true, slot: 'period' },
    ...(r.requested_pickup_date
      ? [
          {
            label: t('reservations.requestedPickup'),
            value: weekday(r.requested_pickup_date),
            mono: true,
          },
        ]
      : []),
    {
      label: t('reservations.pickupAt'),
      value: r.pickup_at ? weekday(r.pickup_at) : null,
      mono: true,
    },
    { label: t('reservations.pickupLocation'), value: r.pickup_location?.full_name },
    {
      label: t('handover.method'),
      value:
        t(`handover.mode.${r.handover_mode}`) +
        (r.handover_mode === 'pickup' && r.skip_device_check
          ? ` · ${t('handover.withoutCheck')}`
          : ''),
    },
    { label: t('reservations.handledBy'), value: r.handled_by?.display_name },
    { label: t('common.createdAt'), value: date(r.created_at), mono: true },
    ...(r.notes ? [{ label: t('reservations.notes'), value: r.notes, wide: true }] : []),
    ...(r.it_comment
      ? [{ label: t('reservations.itComment'), value: r.it_comment, wide: true }]
      : []),
  ]
})
</script>

<template>
  <DetailGrid :entries="entries">
    <template #period>
      <span class="mono">{{ period }}</span>
      <span v-if="reservation.is_overdue" class="overdue"> · {{ t('reservations.overdue') }}</span>
    </template>
  </DetailGrid>
</template>

<style scoped>
.overdue {
  color: var(--ar-error);
  font-weight: 600;
}
</style>
