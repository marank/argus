<script setup lang="ts">
import { CalendarRange } from '@lucide/vue'
import { NRadioButton, NRadioGroup } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import DateField from '@/components/common/DateField.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'

import type { RequestPeriod } from './types'

/** Duration and dates of the request, above the cart; the catalog's availability follows it. */
defineProps<{ showsAvailability: boolean }>()
const period = defineModel<RequestPeriod>({ required: true })
const { t } = useI18n()

const today = new Date().setHours(0, 0, 0, 0)
const beforeToday = (ts: number) => ts < today
</script>

<template>
  <section class="period">
    <header>
      <CalendarRange :size="16" />
      <h2>{{ t('reservations.new.period') }}</h2>
    </header>
    <div class="fields">
      <div class="field">
        <FieldLabel :label="t('reservations.duration')" :help="t('reservations.new.durationHelp')" />
        <NRadioGroup v-model:value="period.duration" size="small" class="duration">
          <NRadioButton value="temporary">{{ t('enums.duration.temporary') }}</NRadioButton>
          <NRadioButton value="permanent">{{ t('enums.duration.permanent') }}</NRadioButton>
        </NRadioGroup>
      </div>
      <div class="field">
        <FieldLabel
          :label="
            period.duration === 'temporary' ? t('reservations.period') : t('reservations.startDate')
          "
        />
        <DateField
          v-if="period.duration === 'temporary'"
          v-model:value="period.range"
          type="daterange"
          size="small"
          :is-date-disabled="beforeToday"
          style="width: 100%"
        />
        <DateField
          v-else
          v-model:value="period.start"
          type="date"
          size="small"
          :is-date-disabled="beforeToday"
          style="width: 100%"
        />
      </div>
    </div>
    <small v-if="showsAvailability" class="muted">{{ t('reservations.new.periodHint') }}</small>
  </section>
</template>

<style scoped>
.period {
  display: grid;
  gap: 10px;
  padding: 14px 18px 16px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ar-text-muted);
}
h2 {
  margin: 0;
  color: var(--ar-text);
  font-size: 14px;
  font-weight: 600;
}
.fields {
  display: grid;
  gap: 10px;
}
.field {
  display: grid;
  gap: 4px;
}
.duration {
  display: flex;
  width: 100%;
}
.duration :deep(.n-radio-button) {
  flex: 1;
  text-align: center;
}
small {
  font-size: 11.5px;
}
</style>
