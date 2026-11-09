<script setup lang="ts">
import { NSwitch } from 'naive-ui'

/**
 * A switch as a full-width row: label and explanation left, switch right; rows divide by lines.
 * A refused value (`error`) marks the label red; the error popover shows the message.
 */
defineProps<{ label: string; help?: string; error?: string; disabled?: boolean }>()
const value = defineModel<boolean>({ default: false })
</script>

<template>
  <label class="toggle" :class="{ invalid: error }" :data-field-error="error || undefined">
    <span class="text">
      <span class="label">{{ label }}</span>
      <small v-if="help" class="muted">{{ help }}</small>
    </span>
    <NSwitch v-model:value="value" :disabled="disabled" />
  </label>
</template>

<style scoped>
.toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 9px 0;
  cursor: pointer;
}
.toggle + .toggle {
  border-top: 1px solid var(--ar-border);
}
.text {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.label {
  font-size: 13px;
}
small {
  font-size: 11.5px;
  line-height: 1.4;
}
.invalid .label {
  color: var(--ar-error);
}
</style>
