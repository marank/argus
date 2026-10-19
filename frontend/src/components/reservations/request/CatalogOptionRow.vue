<script setup lang="ts">
import { Check, Plus } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { useI18n } from 'vue-i18n'

/** A single requestable option with an add button and the quantity already in the request. */
defineProps<{
  label: string
  hint?: string
  available: number | null
  inCart: number
  primary?: boolean
}>()
const emit = defineEmits<{ add: [] }>()
const { t } = useI18n()
</script>

<template>
  <div class="option" :class="{ primary }">
    <div class="text">
      <span class="label">{{ label }}</span>
      <small v-if="hint" class="muted">{{ hint }}</small>
    </div>
    <span v-if="available !== null" class="mono avail" :class="{ none: !available }">
      {{
        available
          ? t('reservations.new.available', { count: available })
          : t('reservations.new.unavailable')
      }}
    </span>
    <span v-if="inCart" class="in-cart mono">
      <Check :size="13" /> {{ t('reservations.new.inCart', { count: inCart }) }}
    </span>
    <NButton
      :type="primary ? 'primary' : 'default'"
      :secondary="!primary"
      size="small"
      @click="emit('add')"
    >
      <template #icon><Plus :size="14" /></template>
      {{ t('common.add') }}
    </NButton>
  </div>
</template>

<style scoped>
.option {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 9px 12px;
  border-bottom: 1px solid var(--ar-border);
}
.option:last-child {
  border-bottom: none;
}
.option.primary {
  padding: 12px;
  border: 1px solid color-mix(in srgb, var(--ar-primary) 35%, transparent);
  border-radius: 3px;
  background: var(--ar-primary-soft);
}
.text {
  display: grid;
  flex: 1;
  min-width: 0;
}
.primary .label {
  font-weight: 600;
}
.avail {
  font-size: 11px;
  color: var(--ar-success);
  white-space: nowrap;
}
.avail.none {
  color: var(--ar-text-subtle);
}
.in-cart {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--ar-primary);
  white-space: nowrap;
}
</style>
