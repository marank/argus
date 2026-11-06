<script setup lang="ts">
import { NInput } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { formatDateRange, parseDateRange, type DateRange } from '@/utils/dateRange'

/**
 * A date range typed as text ("0611..2311", "06.11..", "..23.11.26", see `utils/dateRange`).
 * On Enter or leaving the field the text is read and shown in its normal form; text that
 * cannot be read stays as typed, marked as an error, and changes nothing.
 */
const props = defineProps<{ value: DateRange; size?: 'small' | 'medium' }>()
const emit = defineEmits<{ 'update:value': [range: DateRange] }>()
const { t } = useI18n()

const text = ref(formatDateRange(props.value))
const invalid = ref(false)

watch(
  () => [props.value.from, props.value.until],
  () => {
    text.value = formatDateRange(props.value)
    invalid.value = false
  },
)

function commit() {
  const range = parseDateRange(text.value)
  if (range === undefined) {
    invalid.value = true
    return
  }
  invalid.value = false
  const next = range ?? { from: null, until: null }
  text.value = formatDateRange(next)
  if (next.from !== props.value.from || next.until !== props.value.until) emit('update:value', next)
}
</script>

<template>
  <NInput
    v-model:value="text"
    class="date-range mono"
    :size="size"
    :status="invalid ? 'error' : undefined"
    :placeholder="t('table.dateRangePlaceholder')"
    :title="invalid ? t('table.dateRangeInvalid') : t('table.dateRangeHelp')"
    clearable
    @blur="commit"
    @keydown.enter.prevent="commit"
    @clear="((text = ''), commit())"
  />
</template>
