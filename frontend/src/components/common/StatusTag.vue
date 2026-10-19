<script setup lang="ts">
import { computed } from 'vue'

import { useFormat } from '@/composables/useFormat'
import { toneOf } from '@/utils/status'

/** pulse: animate the dot where the status waits for action (opt-in per place). */
const props = defineProps<{ group: string; value: string; pulse?: boolean }>()
const { enumLabel } = useFormat()

const tone = computed(() => toneOf(props.group, props.value))
</script>

<template>
  <span class="status-tag" :data-tone="tone">
    <span class="dot" :class="{ pulse }" />
    {{ enumLabel(group, value) }}
  </span>
</template>

<style scoped>
.status-tag {
  --tone: var(--ar-text-muted);
  display: inline-flex;
  /* Keep its own width inside grid and flex layouts. */
  justify-self: start;
  align-self: center;
  width: max-content;
  align-items: center;
  gap: 6px;
  padding: 1px 7px 1px 6px;
  border: 1px solid color-mix(in srgb, var(--tone) 35%, transparent);
  background: color-mix(in srgb, var(--tone) 9%, transparent);
  color: var(--tone);
  border-radius: 2px;
  font-size: 11.5px;
  font-weight: 600;
  line-height: 18px;
  white-space: nowrap;
}
.dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.dot.pulse {
  animation: ar-pulse-ring 1.8s ease-out infinite;
}
[data-tone='info'] {
  --tone: var(--ar-info);
}
[data-tone='success'] {
  --tone: var(--ar-success);
}
[data-tone='warning'] {
  --tone: var(--ar-warning);
}
[data-tone='error'] {
  --tone: var(--ar-error);
}
[data-tone='primary'] {
  --tone: var(--ar-primary);
}
</style>
