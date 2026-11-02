<script setup lang="ts">
import { Minus, Plus } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import type { Schemas } from '@/api/types'

/**
 * A single requestable option: an add button, and once it is in the request a stepper
 * with the quantity, so it can be changed right here.
 */
defineProps<{
  label: string
  hint?: string
  /** Availability in the request period (IT only). */
  counts: Schemas['CountsOut'] | null
  inCart: number
  primary?: boolean
}>()
const emit = defineEmits<{ add: []; remove: [] }>()
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
              ? t('requests.new.available', { count: counts.available })
              : t('requests.new.unavailable')
          }}
        </span>
        <span v-if="counts?.reserved" class="reserved">
          {{ t('requests.new.reserved', { count: counts.reserved }) }}
        </span>
      </span>
    </div>
    <div v-if="inCart" class="stepper">
      <NButton
        secondary
        size="small"
        class="less"
        :aria-label="t('requests.new.oneLess', { label })"
        @click="emit('remove')"
      >
        <template #icon><Minus :size="14" /></template>
      </NButton>
      <span
        :key="inCart"
        class="in-cart mono"
        :title="t('requests.new.inCart', { count: inCart })"
        >{{ inCart }}</span
      >
      <NButton
        secondary
        size="small"
        class="add"
        :aria-label="`${t('common.add')}: ${label}`"
        @click="emit('add')"
      >
        <template #icon><Plus :size="14" /></template>
      </NButton>
    </div>
    <NButton
      v-else
      :type="primary ? 'primary' : 'default'"
      :secondary="!primary"
      size="small"
      class="add first"
      :aria-label="`${t('common.add')}: ${label}`"
      @click="emit('add')"
    >
      <template #icon><Plus :size="14" /></template>
      <span class="add-label">{{ t('common.add') }}</span>
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
/* Minus, count, plus: as wide as the add button it replaces, so the row does not jump. */
.stepper {
  display: flex;
  align-items: center;
  flex: none;
  border-radius: 3px;
  background: var(--ar-primary-soft);
}
.stepper .n-button {
  width: 30px;
  padding: 0;
}
.stepper :deep(.n-button__icon) {
  margin: 0;
}
.in-cart {
  /* Re-keyed on every change, so the pop plays when the quantity changes. */
  animation: ar-pop 0.25s ease-out;
  min-width: 28px;
  color: var(--ar-primary);
  font-size: 13px;
  font-weight: 700;
  text-align: center;
}
/*
 * A narrow column (a phone, or the middle of three on a small screen): a plain plus,
 * square so it sits in the middle, and a short count, so the name keeps the room.
 */
@container catalog (max-width: 480px) {
  .option {
    gap: 10px;
    padding-inline: 10px;
  }
  .add-label {
    display: none;
  }
  .add.first {
    width: 32px;
    padding: 0;
  }
  .add.first :deep(.n-button__icon) {
    margin: 0;
  }
}
</style>
