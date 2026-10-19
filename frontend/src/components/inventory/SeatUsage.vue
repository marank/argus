<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

/** Used and total seats of a license as a short bar. */
const props = defineProps<{ used: number; seats: number }>()
const { t } = useI18n()

const ratio = computed(() => (props.seats ? Math.min(props.used / props.seats, 1) : 0))
const tone = computed(() => (ratio.value >= 1 ? 'full' : ratio.value >= 0.85 ? 'tight' : 'ok'))
</script>

<template>
  <div class="seats" :class="tone">
    <span class="mono">{{ t('inventory.licenses.seatsUsed', { used, seats }) }}</span>
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
