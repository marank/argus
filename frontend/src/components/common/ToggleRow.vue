<script setup lang="ts">
import { NSwitch } from 'naive-ui'

/** A switch as a full-width row: label and explanation left, switch right; rows divide by lines. */
defineProps<{ label: string; help?: string; error?: string; disabled?: boolean }>()
const value = defineModel<boolean>({ default: false })
</script>

<template>
  <label class="toggle">
    <span class="text">
      <span class="label">{{ label }}</span>
      <small v-if="help" class="muted">{{ help }}</small>
      <small v-if="error" class="error">{{ error }}</small>
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
.error {
  color: var(--ar-error);
}
</style>
