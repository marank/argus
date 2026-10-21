<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

/**
 * Used and total seats of a license as a short bar. In a table, pass the most digits of all
 * rows as `digits`: the numbers are padded to it, so slashes, text and bars line up.
 */
const props = defineProps<{ used: number; seats: number; digits?: number }>()
const { t } = useI18n()

const ratio = computed(() => (props.seats ? Math.min(props.used / props.seats, 1) : 0))
const tone = computed(() => (ratio.value >= 1 ? 'full' : ratio.value >= 0.85 ? 'tight' : 'ok'))
// Monospace with whitespace kept, so padding with spaces aligns the digits.
const pad = (n: number) => String(n).padStart(props.digits ?? 0, ' ')
</script>

<template>
  <div class="seats" :class="tone">
    <span class="mono count">{{
      t('inventory.licenses.seatsUsed', { used: pad(used), seats: pad(seats) })
    }}</span>
    <span class="bar"><span :style="{ width: `${ratio * 100}%` }" /></span>
  </div>
</template>

<style scoped>
.seats {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}
.count {
  white-space: pre;
}
.bar {
  flex: 0 0 56px;
  height: 4px;
  border-radius: 2px;
  background: var(--ar-border);
  overflow: hidden;
}
.bar span {
  display: block;
  height: 100%;
  transition:
    width 0.3s ease,
    background-color 0.3s ease;
  background: var(--ar-success);
}
.tight .bar span {
  background: var(--ar-warning);
}
.full .bar span {
  background: var(--ar-error);
}
</style>
