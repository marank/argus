<script setup lang="ts">
import { NCard, NRadioButton, NRadioGroup, NSkeleton } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import StatusTag from '@/components/common/StatusTag.vue'
import type { UpcomingHandout, WidgetProps } from '@/types/dashboard'

import { useDateMode } from './dateMode'
import DateModeToggle from './DateModeToggle.vue'
import { oneOf, PERIODS, useOption, type Period } from './options'
import WidgetOptions from './WidgetOptions.vue'

const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const { t } = useI18n()
const stored = () => props.options
const save = (options: Record<string, unknown>) => emit('update:options', options)
const { mode, setMode, when, other } = useDateMode(stored, save)
const days = useOption<Period>(stored, save, 'days', 7, oneOf(PERIODS))

const rows = ref<UpcomingHandout[] | null>(null)
watch(days, async (value) => (rows.value = await dashboardApi.upcoming(value)), {
  immediate: true,
})
</script>

<template>
  <NCard :title="title ?? t('dashboard.upcomingDays', { count: days })" size="small">
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
    <p v-else-if="!rows.length" class="muted">{{ t('dashboard.noUpcoming') }}</p>
    <div v-else class="lines dated">
      <RouterLink
        v-for="r in rows"
        :key="r.id"
        :to="{ name: 'reservation', params: { id: r.id } }"
        class="line"
      >
        <span class="mono">{{ r.number }}</span>
        <span class="title"
          >{{ r.title }}<small class="muted"> · {{ r.requester.display_name }}</small></span
        >
        <span
          class="when"
          :class="{ 'mono muted full': mode === 'full' }"
          :title="other(r.pickup_at ?? r.start_date)"
          >{{ when(r.pickup_at ?? r.start_date) }}</span
        >
        <!-- Pending hand-outs wait for IT: the dot pulses. -->
        <StatusTag group="reservationStatus" :value="r.status" pulse />
      </RouterLink>
    </div>
  </NCard>
</template>

<style scoped src="./lines.css"></style>
