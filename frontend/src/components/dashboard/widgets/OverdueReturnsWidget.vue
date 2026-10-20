<script setup lang="ts">
import { Mail } from '@lucide/vue'
import { NButton, NCard, NSkeleton } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import { useFormat } from '@/composables/useFormat'
import type { OverdueReturn, WidgetProps } from '@/types/dashboard'

import { useDateMode } from './dateMode'
import DateModeToggle from './DateModeToggle.vue'
import { useRemind } from './remind'

const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const { t } = useI18n()
const { date, dateWithWeekday } = useFormat()
const { mode, setMode } = useDateMode(
  () => props.options,
  (options) => emit('update:options', options),
)
const rows = ref<OverdueReturn[] | null>(null)

const load = async () => (rows.value = await dashboardApi.overdueReturns())
onMounted(load)
const { remind, sending } = useRemind(load)

const daysOverdue = (row: OverdueReturn) =>
  Math.round((Date.now() - new Date(`${row.end_date}T00:00:00`).getTime()) / 86_400_000)
</script>

<template>
  <NCard :title="t('dashboard.widgets.overdueReturns.title')" size="small">
    <template #header-extra>
      <span class="header-extra">
        <RouterLink
          v-if="rows?.length"
          :to="{ name: 'reservations', query: { overdue: '1' } }"
          class="mono muted"
        >
          {{ rows.length }}
        </RouterLink>
        <DateModeToggle :model-value="mode" @update:model-value="setMode" />
      </span>
    </template>
    <NSkeleton v-if="!rows" text :repeat="3" />
    <p v-else-if="!rows.length" class="muted">{{ t('dashboard.widgets.overdueReturns.empty') }}</p>
    <div v-else class="lines cols-4">
      <div v-for="row in rows" :key="row.id" class="line">
        <RouterLink :to="{ name: 'reservation', params: { id: row.id } }" class="mono">
          {{ row.number }}
        </RouterLink>
        <span class="title">
          {{ row.requester.display_name }}<small class="muted"> · {{ row.title }}</small>
          <small v-if="row.reminded_at" class="muted reminded">
            {{ t('dashboard.widgets.overdueReturns.reminded', { date: date(row.reminded_at) }) }}
          </small>
        </span>
        <span
          class="mono overdue"
          :title="
            mode === 'full'
              ? t('dashboard.widgets.overdueReturns.days', { count: daysOverdue(row) })
              : dateWithWeekday(row.end_date)
          "
        >
          {{
            mode === 'full'
              ? t('dashboard.widgets.overdueReturns.due', { date: dateWithWeekday(row.end_date) })
              : t('dashboard.widgets.overdueReturns.days', { count: daysOverdue(row) })
          }}
        </span>
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
.header-extra {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.overdue {
  color: var(--ar-error);
}
</style>
