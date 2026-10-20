<script setup lang="ts">
import { Table2, ChartColumn } from '@lucide/vue'
import { NButton, NCard, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import type { TrendWeek, WidgetProps } from '@/types/dashboard'

import { isBoolean, useOption } from './options'

const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const { t } = useI18n()
const { date } = useFormat()
const weeks = ref<TrendWeek[] | null>(null)
const asTable = useOption(
  () => props.options,
  (options) => emit('update:options', options),
  'as_table',
  false,
  isBoolean,
)
const active = ref<number | null>(null)

const load = async () => (weeks.value = await dashboardApi.requestTrend())
onMounted(load)
useLive(['reservation'], load)

const SERIES = [
  { key: 'created', label: 'dashboard.widgets.requestTrend.created', color: 'var(--ar-series-1)' },
  {
    key: 'completed',
    label: 'dashboard.widgets.requestTrend.completed',
    color: 'var(--ar-series-2)',
  },
] as const

/** A clean top for the axis: 1, 2 or 5 times a power of ten, at least 4. */
const top = computed(() => {
  const max = Math.max(4, ...(weeks.value ?? []).flatMap((w) => [w.created, w.completed]))
  const step = 10 ** Math.floor(Math.log10(max))
  return [1, 2, 5, 10].map((f) => f * step).find((v) => v >= max)!
})
const ticks = computed(() => [0, top.value / 2, top.value])
const totals = computed(() => ({
  created: (weeks.value ?? []).reduce((sum, w) => sum + w.created, 0),
  completed: (weeks.value ?? []).reduce((sum, w) => sum + w.completed, 0),
}))

/** ISO 8601 week number: the week belongs to the year its Thursday is in. */
function weekNumber(monday: string) {
  const day = new Date(`${monday}T00:00:00Z`)
  day.setUTCDate(day.getUTCDate() + 3)
  const yearStart = Date.UTC(day.getUTCFullYear(), 0, 1)
  return Math.ceil(((day.getTime() - yearStart) / 86_400_000 + 1) / 7)
}

const weekLabel = (w: TrendWeek) =>
  t('dashboard.widgets.requestTrend.week', { n: weekNumber(w.week_start) })
const describe = (w: TrendWeek) =>
  `${weekLabel(w)} (${date(w.week_start)}): ${SERIES.map((s) => `${t(s.label)} ${w[s.key]}`).join(', ')}`
</script>

<template>
  <NCard :title="t('dashboard.widgets.requestTrend.title')" size="small">
    <template #header-extra>
      <NButton
        quaternary
        size="tiny"
        :title="
          asTable
            ? t('dashboard.widgets.requestTrend.chart')
            : t('dashboard.widgets.requestTrend.table')
        "
        @click="asTable = !asTable"
      >
        <template #icon><component :is="asTable ? ChartColumn : Table2" /></template>
      </NButton>
    </template>
    <NSkeleton v-if="!weeks" height="150px" />
    <template v-else>
      <ul class="legend">
        <li v-for="s in SERIES" :key="s.key">
          <span class="swatch" :style="{ background: s.color }" />
          {{ t(s.label) }} <span class="mono">{{ totals[s.key] }}</span>
        </li>
      </ul>
      <table v-if="asTable" class="table">
        <thead>
          <tr>
            <th>{{ t('dashboard.widgets.requestTrend.weekColumn') }}</th>
            <th v-for="s in SERIES" :key="s.key" class="num">{{ t(s.label) }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="w in [...weeks].reverse()" :key="w.week_start">
            <td>
              {{ weekLabel(w) }} <small class="muted">{{ date(w.week_start) }}</small>
            </td>
            <td v-for="s in SERIES" :key="s.key" class="num mono">{{ w[s.key] }}</td>
          </tr>
        </tbody>
      </table>
      <div v-else class="chart">
        <div class="axis mono muted">
          <span v-for="tick in [...ticks].reverse()" :key="tick">{{ tick }}</span>
        </div>
        <div class="plot" @mouseleave="active = null">
          <span
            v-for="tick in ticks"
            :key="tick"
            class="grid"
            :style="{ bottom: `${(tick / top) * 100}%` }"
          />
          <div
            v-for="(w, index) in weeks"
            :key="w.week_start"
            class="band"
            tabindex="0"
            :aria-label="describe(w)"
            @mouseenter="active = index"
            @focus="active = index"
            @blur="active = null"
          >
            <div class="bars">
              <span
                v-for="s in SERIES"
                :key="s.key"
                class="bar"
                :style="{ height: `${(w[s.key] / top) * 100}%`, background: s.color }"
              />
            </div>
            <span class="label mono muted">{{
              index % 2 === weeks.length % 2 ? '' : weekNumber(w.week_start)
            }}</span>
            <div
              v-if="active === index"
              class="tooltip"
              :class="{ left: index > weeks.length / 2 }"
            >
              <strong>{{ weekLabel(w) }}</strong>
              <small class="muted">{{ date(w.week_start) }}</small>
              <span v-for="s in SERIES" :key="s.key" class="tip-row">
                <span class="swatch" :style="{ background: s.color }" />
                {{ t(s.label) }}
                <span class="mono">{{ w[s.key] }}</span>
              </span>
            </div>
          </div>
        </div>
      </div>
    </template>
  </NCard>
</template>

<style scoped>
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 16px;
  margin: 0 0 10px;
  padding: 0;
  list-style: none;
  font-size: 12px;
}
.legend li,
.tip-row {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  /* An entry wraps to the next line as a whole, never inside a word. */
  white-space: nowrap;
}
.swatch {
  flex: none;
}
.swatch {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}
.chart {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 8px;
}
.axis {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  height: 130px;
  font-size: 11px;
  text-align: right;
  /* The numbers sit on their gridlines. */
  margin-top: -7px;
}
.plot {
  position: relative;
  display: flex;
  height: 130px;
  margin-bottom: 18px;
}
.grid {
  position: absolute;
  right: 0;
  left: 0;
  height: 1px;
  background: var(--ar-border);
}
.band {
  position: relative;
  display: flex;
  flex: 1;
  flex-direction: column;
  justify-content: flex-end;
  min-width: 0;
  outline: none;
}
.band:hover,
.band:focus-visible {
  background: color-mix(in srgb, var(--ar-text) 5%, transparent);
}
.bars {
  display: flex;
  align-items: flex-end;
  justify-content: center;
  gap: 2px;
  height: 100%;
}
/* Square at the baseline, rounded at the data end. */
.bar {
  position: relative;
  width: min(12px, 40%);
  border-radius: 4px 4px 0 0;
}
.label {
  position: absolute;
  top: 100%;
  right: 0;
  left: 0;
  padding-top: 3px;
  font-size: 10px;
  text-align: center;
}
.tooltip {
  position: absolute;
  bottom: calc(100% + 4px);
  left: 50%;
  z-index: 2;
  display: grid;
  gap: 2px;
  min-width: 150px;
  padding: 8px 10px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  box-shadow: 0 4px 14px rgb(0 0 0 / 0.12);
  font-size: 12px;
  pointer-events: none;
}
.tooltip.left {
  right: 50%;
  left: auto;
}
.tip-row .mono {
  margin-left: auto;
}
.table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.table th,
.table td {
  padding: 4px 6px;
  border-bottom: 1px solid var(--ar-border);
  text-align: left;
}
.table th {
  color: var(--ar-text-subtle);
  font-weight: 500;
}
.table .num {
  text-align: right;
}
</style>
