<script setup lang="ts">
import { CircleHelp } from '@lucide/vue'
import { NTooltip } from 'naive-ui'

/**
 * Form label for the `#label` slot of NFormItem: text, required mark and, right-aligned,
 * an optional live value (`#extra`) and a help icon that shows `help` on hover/tap.
 */
defineProps<{ label: string; help?: string; required?: boolean }>()
</script>

<template>
  <span class="field-label">
    <span class="text">
      {{ label }}<span v-if="required" class="required" aria-hidden="true">*</span>
    </span>
    <span v-if="$slots.extra" class="extra mono"><slot name="extra" /></span>
    <NTooltip
      v-if="help"
      trigger="hover"
      placement="top-end"
      :show-arrow="false"
      :style="{ maxWidth: '320px' }"
    >
      <template #trigger>
        <span class="help" tabindex="0" role="button" :aria-label="help">
          <CircleHelp :size="14" :stroke-width="1.8" />
        </span>
      </template>
      {{ help }}
    </NTooltip>
  </span>
</template>

<style scoped>
.field-label {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}
.text {
  flex: 1;
  min-width: 0;
}
.required {
  margin-left: 3px;
  color: var(--ar-error);
}
.extra {
  font-size: 11px;
  color: var(--ar-text-muted);
}
.help {
  display: inline-flex;
  color: var(--ar-text-subtle);
  cursor: help;
  border-radius: 50%;
  outline: none;
}
.help:hover,
.help:focus-visible {
  color: var(--ar-primary);
}
</style>
