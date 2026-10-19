<script setup lang="ts">
import { Check, Plus } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import type { AvailabilityCounts } from '@/types/reservations'

/** A single requestable option with an add button and the quantity already in the request. */
defineProps<{
  label: string
  hint?: string
  /** Availability in the request period (IT only). */
  counts: AvailabilityCounts | null
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
      <!-- Hint and availability (IT only) as one quiet line under the name. -->
      <span v-if="hint || counts" class="meta">
        <span v-if="hint" class="muted">{{ hint }}</span>
        <span v-if="counts" class="avail" :class="{ none: !counts.available }">
          <span class="avail-dot" />
          {{
            counts.available
              ? t('reservations.new.available', { count: counts.available })
              : t('reservations.new.unavailable')
          }}
        </span>
        <span v-if="counts?.reserved" class="reserved">
          {{ t('reservations.new.reserved', { count: counts.reserved }) }}
        </span>
      </span>
    </div>
    <span v-if="inCart" :key="inCart" class="in-cart mono">
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
.meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 2px 10px;
  font-size: 11.5px;
}
.avail {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  color: var(--ar-success);
  white-space: nowrap;
}
.reserved {
  color: var(--ar-text-subtle);
  white-space: nowrap;
}
.reserved::before {
  content: '·';
  margin-right: 8px;
}
.avail.none {
  color: var(--ar-text-subtle);
}
.avail-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
}
.in-cart {
  /* Re-keyed on every change, so the pop plays when something is added. */
  animation: ar-pop 0.25s ease-out;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--ar-primary);
  white-space: nowrap;
}
</style>
