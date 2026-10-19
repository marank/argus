<script setup lang="ts">
import { CircleHelp, Lock } from '@lucide/vue'
import { NTooltip } from 'naive-ui'

/**
 * Label (with optional help and "set by environment" lock) next to its control.
 * Rows inside a SettingsGroup are separated by thin lines.
 */
defineProps<{ label: string; help?: string; lockedBy?: string; required?: boolean }>()
</script>

<template>
  <div class="setting-row">
    <div class="label">
      <span> {{ label }}<span v-if="required" class="required" aria-hidden="true">*</span> </span>
      <NTooltip v-if="help" :show-arrow="false" :style="{ maxWidth: '320px' }">
        <template #trigger>
          <span class="icon" tabindex="0" role="button" :aria-label="help">
            <CircleHelp :size="13" :stroke-width="1.8" />
          </span>
        </template>
        {{ help }}
      </NTooltip>
      <NTooltip v-if="lockedBy" :show-arrow="false">
        <template #trigger>
          <span class="icon locked" tabindex="0" role="img" :aria-label="lockedBy">
            <Lock :size="12" :stroke-width="2" />
          </span>
        </template>
        {{ lockedBy }}
      </NTooltip>
    </div>
    <div class="control">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.setting-row {
  display: grid;
  grid-template-columns: minmax(140px, 200px) minmax(0, 1fr);
  align-items: center;
  gap: 6px 16px;
  min-height: 48px;
  padding: 9px 0;
}
.setting-row + .setting-row {
  border-top: 1px solid var(--ar-border);
}
.label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
}
.required {
  margin-left: 3px;
  color: var(--ar-error);
}
.icon {
  display: inline-flex;
  color: var(--ar-text-subtle);
  cursor: help;
  outline: none;
}
.icon:hover,
.icon:focus-visible {
  color: var(--ar-primary);
}
.locked {
  color: var(--ar-warning);
}
.control {
  min-width: 0;
}
@container (max-width: 440px) {
  .setting-row {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
