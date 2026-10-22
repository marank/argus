<script setup lang="ts">
import { CalendarPlus, Mail } from '@lucide/vue'
import { NButton, NCard, NRadioButton, NRadioGroup, NSkeleton } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import ExtendModal from '@/components/requests/ExtendModal.vue'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import type { DueReturn, WidgetProps } from '@/types/dashboard'

import { useDateMode } from './dateMode'
import DateModeToggle from './DateModeToggle.vue'
import { oneOf, useOption } from './options'
import { useRemind } from './remind'
import WidgetOptions from './WidgetOptions.vue'

/** Lendings ending soon, before they turn up under "Overdue returns". */
const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const PERIODS = [3, 7] as const

const { t } = useI18n()
const { date } = useFormat()
const stored = () => props.options
const save = (options: Record<string, unknown>) => emit('update:options', options)
const { mode, setMode, when, other } = useDateMode(stored, save)
const days = useOption<(typeof PERIODS)[number]>(stored, save, 'days', 3, oneOf(PERIODS))

const rows = ref<DueReturn[] | null>(null)
const load = async () => (rows.value = await dashboardApi.dueReturns(days.value))
watch(days, load, { immediate: true })
useLive(['request'], load)
const { remind, sending } = useRemind(load)

const extending = ref<DueReturn | null>(null)
const showExtend = ref(false)
function extend(row: DueReturn) {
  extending.value = row
  showExtend.value = true
}
</script>

<template>
  <NCard :title="title ?? t('dashboard.widgets.dueReturns.title')" size="small">
    <template #header-extra>
      <DateModeToggle :model-value="mode" @update:model-value="setMode" />
      <WidgetOptions>
        <div>
          <span class="eyebrow">{{ t('dashboard.widgets.period') }}</span>
          <NRadioGroup v-model:value="days" size="small">
            <NRadioButton v-for="p in PERIODS" :key="p" :value="p">
              {{ t('dashboard.widgets.days', { count: p }, p) }}
            </NRadioButton>
          </NRadioGroup>
        </div>
      </WidgetOptions>
    </template>
    <NSkeleton v-if="!rows" text :repeat="3" />
    <p v-else-if="!rows.length" class="muted">
      {{ t('dashboard.widgets.dueReturns.empty', { count: days }) }}
    </p>
    <div v-else class="lines cols-5">
      <div v-for="row in rows" :key="row.id" class="line">
        <RouterLink :to="{ name: 'request', params: { id: row.id } }" class="mono">
          {{ row.number }}
        </RouterLink>
        <span class="title">
          {{ row.requester.display_name }}<small class="muted"> · {{ row.title }}</small>
          <small v-if="row.reminded_at" class="muted reminded">
            {{ t('dashboard.widgets.overdueReturns.reminded', { date: date(row.reminded_at) }) }}
          </small>
        </span>
        <span
          class="when"
          :class="{ 'mono muted full': mode === 'full' }"
          :title="other(row.end_date)"
          >{{ when(row.end_date) }}</span
        >
        <NButton
          size="tiny"
          quaternary
          :title="t('requests.actions.extend')"
          @click="extend(row)"
        >
          <template #icon><CalendarPlus /></template>
        </NButton>
        <NButton
          size="tiny"
          :disabled="!row.can_remind"
          :loading="sending === row.id"
          :title="row.can_remind ? undefined : t('dashboard.widgets.overdueReturns.noEmail')"
          @click="remind(row)"
        >
          <template #icon><Mail /></template>
          {{ t('dashboard.widgets.overdueReturns.remind') }}
        </NButton>
      </div>
    </div>
    <ExtendModal
      v-if="extending"
      v-model:show="showExtend"
      :assetRequest="extending"
      @saved="load"
    />
  </NCard>
</template>

<style scoped src="./lines.css"></style>
<style scoped>
.line a {
  color: inherit;
}
.line a:hover {
  color: var(--ar-primary);
}
.reminded {
  display: block;
}
</style>
