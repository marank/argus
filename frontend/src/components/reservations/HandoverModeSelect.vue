<script setup lang="ts">
import { PenLine, Truck } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import type { HandoverMode } from '@/types/reservations'

/** Two large options: pickup with signature at the terminal, or delivery by IT. */
const model = defineModel<HandoverMode>({ required: true })
const { t } = useI18n()

const options = [
  { value: 'pickup' as const, icon: PenLine },
  { value: 'delivery' as const, icon: Truck },
]
</script>

<template>
  <div class="modes" role="radiogroup">
    <button
      v-for="option in options"
      :key="option.value"
      type="button"
      role="radio"
      class="mode"
      :aria-checked="model === option.value"
      :class="{ active: model === option.value }"
      @click="model = option.value"
    >
      <component :is="option.icon" :size="20" :stroke-width="1.6" />
      <span>
        <strong>{{ t(`handover.mode.${option.value}`) }}</strong>
        <small class="muted">{{ t(`handover.modeHint.${option.value}`) }}</small>
      </span>
    </button>
  </div>
</template>

<style scoped>
.modes {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}
.mode {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.mode span {
  display: grid;
  gap: 2px;
}
.mode.active {
  border-color: var(--ar-primary);
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
.mode.active strong {
  color: var(--ar-primary);
}
</style>
