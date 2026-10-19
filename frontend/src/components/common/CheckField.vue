<script setup lang="ts">
import { CircleHelp } from '@lucide/vue'
import { NCheckbox, NTooltip } from 'naive-ui'

/** Checkbox with inline label and optional help tooltip, sized to sit next to inputs. */
defineProps<{ label: string; help?: string }>()
const checked = defineModel<boolean>({ default: false })
</script>

<template>
  <span class="check-field">
    <NCheckbox v-model:checked="checked">{{ label }}</NCheckbox>
    <NTooltip
      v-if="help"
      trigger="hover"
      placement="top-start"
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
.check-field {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 26px;
  white-space: nowrap;
}
.help {
  display: inline-flex;
  color: var(--ar-text-subtle);
  cursor: help;
  outline: none;
}
.help:hover,
.help:focus-visible {
  color: var(--ar-primary);
}
</style>
