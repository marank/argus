<script setup lang="ts">
import { HandHelping, PenLine, Truck } from '@lucide/vue'
import { useI18n } from 'vue-i18n'
import type { Schemas } from '@/api/types'

/** Large options: pickup with signature at the terminal, simple pickup, or delivery by IT. */
const model = defineModel<Schemas['HandoverMode']>({ required: true })
const { t } = useI18n()

const options = [
  { value: 'pickup' as const, icon: PenLine },
  { value: 'collect' as const, icon: HandHelping },
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
      <span class="icon"><component :is="option.icon" :size="18" :stroke-width="1.7" /></span>
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
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}
.mode {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 12px 14px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}
.mode:hover {
  border-color: var(--ar-border-strong);
}
.mode:focus-visible {
  outline: 2px solid var(--ar-primary);
  outline-offset: 2px;
}
/* Fixed size: a two-line hint must not squeeze the icon. */
.icon {
  display: grid;
  flex: none;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 3px;
  background: var(--ar-surface-sunken);
  color: var(--ar-text-muted);
  transition:
    background 0.15s ease,
    color 0.15s ease;
}
.mode span:not(.icon) {
  display: grid;
  gap: 3px;
  padding-top: 1px;
}
.mode small {
  line-height: 1.4;
}
.mode.active {
  border-color: var(--ar-primary);
  background: var(--ar-primary-soft);
}
.mode.active .icon {
  background: var(--ar-primary);
  color: var(--ar-on-primary);
}
.mode.active strong {
  color: var(--ar-primary);
}
</style>
