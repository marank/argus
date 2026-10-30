<script setup lang="ts">
import { NStep, NSteps } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import type { Schemas } from '@/api/types'

const props = defineProps<{ assetRequest: Schemas['AssetRequestOut'] }>()
const { t } = useI18n()

/** Requests that needed the department's approval show it as their first step. */
const steps = computed(() => {
  const list = ['submitted', 'confirmed', 'ready', 'handedOut']
  if (props.assetRequest.approval) list.unshift('approval')
  if (props.assetRequest.duration === 'temporary') list.push('completed')
  return list
})

const STEP_OF: Record<string, string> = {
  pending_approval: 'approval',
  submitted: 'submitted',
  confirmed: 'confirmed',
  ready: 'ready',
  handed_out: 'handedOut',
  completed: 'completed',
}

const current = computed(() => {
  const { status, duration, approval } = props.assetRequest
  let step = STEP_OF[status]
  if (status === 'completed' && duration === 'permanent') step = 'handedOut'
  // Closed early: at the step where it ended – the approval, or IT's decision.
  if (!step) step = approval === 'pending' || approval === 'rejected' ? 'approval' : 'submitted'
  return steps.value.indexOf(step) + 1
})

const stepStatus = computed(() => {
  if (props.assetRequest.status === 'rejected' || props.assetRequest.status === 'cancelled')
    return 'error'
  return props.assetRequest.status === 'completed' ? 'finish' : 'process'
})
</script>

<template>
  <NSteps :current="current" :status="stepStatus" size="small">
    <NStep v-for="step in steps" :key="step" :title="t(`requests.steps.${step}`)" />
  </NSteps>
</template>

<style scoped>
/* The last step has no line after it: let it take only its label, so the bar reaches the end. */
.n-steps :deep(.n-step:last-child) {
  flex: none;
}
</style>
