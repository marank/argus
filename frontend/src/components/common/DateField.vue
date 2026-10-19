<script setup lang="ts">
import { CalendarCheck, Eraser, RotateCcw } from '@lucide/vue'
import { NButton, NDatePicker, NTooltip } from 'naive-ui'
import { computed, h, nextTick, ref, watch, type Component } from 'vue'
import { useI18n } from 'vue-i18n'

import { useSegmentedDateInput } from '@/composables/useSegmentedDateInput'

type Value = number | [number, number] | null

/**
 * NDatePicker with compact icon actions next to "Confirm": today, reset to the
 * value the picker was opened with, and clear (for optional fields).
 * Ranges show a single month.
 */
defineOptions({ inheritAttrs: false })
const props = withDefaults(
  defineProps<{ type?: 'date' | 'datetime' | 'daterange'; clearable?: boolean }>(),
  { type: 'date', clearable: false },
)
const model = defineModel<Value>('value', { default: null })
const { t, locale } = useI18n()

// One fixed-width format per language, shared by the picker and the segment editing.
const format = computed(() => {
  const date = locale.value === 'de' ? 'dd.MM.yyyy' : 'yyyy-MM-dd'
  return props.type === 'datetime' ? `${date} HH:mm` : date
})
const root = ref<HTMLElement | null>(null)
useSegmentedDateInput(root, () => format.value)

const open = ref(false)
const snapshot = ref<Value>(null)
watch(open, (isOpen) => isOpen && (snapshot.value = model.value))

const startOfToday = () => new Date().setHours(0, 0, 0, 0)
const DAY = 86_400_000

function today() {
  if (props.type === 'daterange') {
    const range = model.value as [number, number] | null
    const length = range ? Math.max(range[1] - range[0], 0) : 0
    model.value = [startOfToday(), startOfToday() + Math.round(length / DAY) * DAY]
  } else if (props.type === 'datetime') {
    model.value = Date.now()
  } else {
    model.value = startOfToday()
    open.value = false
  }
}

// The open panel keeps its own pending selection and only resyncs when the bound
// value changes, so reset goes via null to force it back to the opening value.
async function reset() {
  model.value = null
  await nextTick()
  model.value = snapshot.value
}

// "now" and "confirm" are not supported by every panel type; ours replace "now".
const actions = computed<('clear' | 'confirm')[]>(() =>
  props.type === 'date' ? ['clear'] : ['clear', 'confirm'],
)

function iconButton(icon: Component, label: string, onClick: () => void, disabled = false) {
  return h(
    NTooltip,
    { showArrow: false },
    {
      trigger: () =>
        h(
          NButton,
          { size: 'tiny', quaternary: true, disabled, 'aria-label': label, onClick },
          { icon: () => h(icon, { size: 14 }) },
        ),
      default: () => label,
    },
  )
}
</script>

<template>
  <div ref="root" class="date-field">
    <NDatePicker
      v-bind="$attrs"
      :format="format"
      v-model:value="model"
      v-model:show="open"
      :type="type"
      :clearable="clearable"
      :actions="actions"
      :bind-calendar-months="type === 'daterange'"
    >
      <template #clear="{ onClear }">
        <span class="date-actions">
          <component :is="iconButton(CalendarCheck, t('common.today'), today)" />
          <component :is="iconButton(RotateCcw, t('common.resetValue'), reset)" />
          <component :is="iconButton(Eraser, t('common.clear'), onClear)" v-if="clearable" />
        </span>
      </template>
    </NDatePicker>
  </div>
</template>

<style scoped>
.date-field {
  display: contents;
}
/* Pushes the icons to the left edge; "Confirm" stays on the right. */
.date-actions {
  display: inline-flex;
  gap: 2px;
  margin-right: auto;
}
</style>
