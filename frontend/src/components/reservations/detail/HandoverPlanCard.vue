<script setup lang="ts">
import { NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import DetailGrid, { type DetailEntry } from '@/components/common/DetailGrid.vue'
import { useFormat } from '@/composables/useFormat'
import type { Reservation } from '@/types/reservations'

/**
 * How the devices will reach the employee, until they are handed out.
 * `forEmployee` leaves out IT's own notes (who prepared it, what to do next).
 */
const props = defineProps<{ reservation: Reservation; forEmployee?: boolean }>()
const { t } = useI18n()
const { weekday } = useFormat()

const entries = computed<DetailEntry[]>(() => {
  const r = props.reservation
  return [
    {
      label: t('handover.method'),
      value:
        t(`handover.mode.${r.handover_mode}`) +
        (r.handover_mode === 'pickup' && r.skip_device_check
          ? ` · ${t('handover.withoutCheck')}`
          : ''),
      wide: true,
    },
    {
      label: r.handover_mode === 'delivery' ? t('handover.deliveryAt') : t('reservations.pickupAt'),
      value: r.pickup_at ? weekday(r.pickup_at) : null,
      mono: true,
    },
    { label: t('reservations.pickupLocation'), value: r.pickup_location?.full_name },
    ...(r.status === 'ready' && !props.forEmployee
      ? [{ label: t('reservations.detail.preparedBy'), value: r.prepared_by?.display_name }]
      : []),
  ]
})

/** What happens next, once everything is prepared. */
const next = computed(() => {
  const r = props.reservation
  if (r.status !== 'ready' || props.forEmployee) return null
  if (r.handover_mode === 'pickup')
    return [t('handover.waitingAtTerminal'), r.skip_device_check ? t('handover.checkSkipped') : '']
      .filter(Boolean)
      .join(' ')
  return r.handover_mode === 'collect'
    ? t('handover.collectPending')
    : t('handover.deliveryPending')
})
</script>

<template>
  <NCard :title="t('handover.title')" size="small">
    <DetailGrid :entries="entries" />
    <p v-if="next" class="next">{{ next }}</p>
  </NCard>
</template>

<style scoped>
.next {
  margin: 14px 0 0;
  padding: 8px 10px;
  border-left: 2px solid var(--ar-primary);
  background: var(--ar-surface-sunken);
  font-size: 12.5px;
}
</style>
