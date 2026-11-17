<script setup lang="ts">
import { NSelect } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import DateField from './DateField.vue'

/**
 * Date and time as two fields side by side: the calendar picks the day, the select next
 * to it the time in quarter hours between 6 and 20 o'clock. A time off that grid (set
 * elsewhere) is listed as well, so it shows unchanged.
 */
const props = withDefaults(defineProps<{ clearable?: boolean }>(), { clearable: false })
const model = defineModel<number | null>('value', { default: null })
const { t } = useI18n()

const FIRST_HOUR = 6
const LAST_HOUR = 20
const DEFAULT_TIME = '09:00'

const pad = (n: number) => String(n).padStart(2, '0')
const timeOf = (date: Date) => `${pad(date.getHours())}:${pad(date.getMinutes())}`

const day = computed<number | null>({
  get: () => (model.value === null ? null : new Date(model.value).setHours(0, 0, 0, 0)),
  set: (value) => {
    model.value = value === null ? null : at(value, time.value ?? DEFAULT_TIME)
  },
})

const time = computed<string | null>({
  get: () => (model.value === null ? null : timeOf(new Date(model.value))),
  set: (value) => {
    if (value === null) return
    model.value = at(day.value ?? new Date().setHours(0, 0, 0, 0), value)
  },
})

function at(dayStart: number, hhmm: string): number {
  const [hours, minutes] = hhmm.split(':').map(Number)
  return new Date(dayStart).setHours(hours!, minutes!, 0, 0)
}

const options = computed(() => {
  const slots: string[] = []
  for (let h = FIRST_HOUR; h <= LAST_HOUR; h++) {
    for (const m of [0, 15, 30, 45]) {
      if (h === LAST_HOUR && m > 0) break
      slots.push(`${pad(h)}:${pad(m)}`)
    }
  }
  if (time.value && !slots.includes(time.value)) slots.push(time.value)
  return slots.sort().map((s) => ({ label: s, value: s }))
})
</script>

<template>
  <div class="date-time">
    <DateField v-model:value="day" :clearable="props.clearable" style="flex: 1; min-width: 0" />
    <NSelect
      v-model:value="time"
      :options="options"
      :aria-label="t('common.time')"
      :placeholder="t('common.time')"
      filterable
      class="time"
    />
  </div>
</template>

<style scoped>
.date-time {
  display: flex;
  gap: 8px;
  width: 100%;
}
.time {
  width: 96px;
  flex: none;
}
.time :deep(.n-base-selection-label) {
  font-family: var(--ar-font-mono);
}
</style>
