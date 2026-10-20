<script setup lang="ts">
import { NStep, NSteps } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Reservation } from '@/types/reservations'

const props = defineProps<{ reservation: Reservation }>()
const { t } = useI18n()

const steps = computed(() => {
  const list = ['submitted', 'approved', 'ready', 'handedOut']
  if (props.reservation.duration === 'temporary') list.push('completed')
  return list
})

const ORDER: Record<string, number> = {
  submitted: 1,
  approved: 2,
  ready: 3,
  handed_out: 4,
  completed: 5,
}

const current = computed(() => {
  const status = props.reservation.status
  if (status === 'completed' && props.reservation.duration === 'permanent') return 4
  return ORDER[status] ?? 1
})

const stepStatus = computed(() => {
  if (props.reservation.status === 'rejected' || props.reservation.status === 'cancelled')
    return 'error'
  return props.reservation.status === 'completed' ? 'finish' : 'process'
})
</script>

<template>
  <NSteps :current="current" :status="stepStatus" size="small">
    <NStep v-for="step in steps" :key="step" :title="t(`reservations.steps.${step}`)" />
  </NSteps>
</template>

<style scoped>
/* The last step has no line after it: let it take only its label, so the bar reaches the end. */
.n-steps :deep(.n-step:last-child) {
  flex: none;
}
</style>
