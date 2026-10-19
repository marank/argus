<script setup lang="ts">
import { ChevronLeft, ChevronRight } from '@lucide/vue'
import FullCalendar from '@fullcalendar/vue3'
import type { CalendarOptions, EventInput, EventSourceFuncInfo } from '@fullcalendar/vue3'
import dayGridPlugin from '@fullcalendar/vue3/daygrid'
import listPlugin from '@fullcalendar/vue3/list'
import deLocale from '@fullcalendar/vue3/locales/de'
import classicTheme from '@fullcalendar/vue3/themes/classic'
import timeGridPlugin from '@fullcalendar/vue3/timegrid'
import '@fullcalendar/vue3/skeleton.css'
import '@fullcalendar/vue3/themes/classic/theme.css'
import { useStorage } from '@vueuse/core'
import { NButton, NButtonGroup, NRadioButton, NRadioGroup, NTooltip } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { calendarApi } from '@/api/calendar'
import PageHeader from '@/components/common/PageHeader.vue'
import { entryColor, isTentative, KIND_ICONS, kindColor } from '@/components/calendar/kinds'
import { toIsoDate, useFormat } from '@/composables/useFormat'
import { useTheme } from '@/theme/useTheme'
import { CALENDAR_KINDS, type CalendarEntry, type CalendarKind } from '@/types/calendar'

/**
 * Planning calendar for IT: lending periods, pickup appointments, due returns,
 * expected deliveries and warranty ends. Permanent hand-outs are not shown.
 */
type ViewName = 'dayGridMonth' | 'timeGridWeek' | 'listMonth'

const { t, locale } = useI18n()
const router = useRouter()
const { date, enumLabel } = useFormat()
const { isDark } = useTheme()

const calendar = ref<InstanceType<typeof FullCalendar> | null>(null)
const view = useStorage<ViewName>('argus.calendar-view', 'dayGridMonth')
const enabled = useStorage<CalendarKind[]>('argus.calendar-kinds', [...CALENDAR_KINDS])
const title = ref('')
const loading = ref(false)

const api = () => calendar.value?.getApi()

function label(entry: CalendarEntry): string {
  switch (entry.kind) {
    case 'pickup':
      return t('calendar.titles.pickup', { name: entry.title })
    case 'return':
      return t('calendar.titles.return', { name: entry.title })
    case 'delivery':
      return t('calendar.titles.delivery', { supplier: entry.title })
    case 'warranty':
      return t('calendar.titles.warranty', { count: Number(entry.title) }, Number(entry.title))
    default:
      return entry.title
  }
}

async function fetchEvents(info: EventSourceFuncInfo): Promise<EventInput[]> {
  if (!enabled.value.length) return []
  loading.value = true
  try {
    const entries = await calendarApi.entries(
      toIsoDate(info.start)!,
      toIsoDate(info.end)!,
      enabled.value,
    )
    return entries.map((entry) => ({
      id: entry.id,
      title: label(entry),
      start: entry.start,
      end: entry.end ?? undefined,
      allDay: entry.all_day,
      color: entryColor(entry),
      className: isTentative(entry) ? 'ar-tentative' : undefined,
      extendedProps: { entry },
    }))
  } finally {
    loading.value = false
  }
}

function open(entry: CalendarEntry) {
  if (entry.link.name === 'assets') {
    router.push({ name: 'assets', query: { warranty_until: entry.link.warranty_until } })
  } else if (entry.link.id) {
    router.push({ name: entry.link.name, params: { id: entry.link.id } })
  }
}

const options = computed<CalendarOptions>(() => ({
  plugins: [classicTheme, dayGridPlugin, timeGridPlugin, listPlugin],
  initialView: view.value,
  headerToolbar: false,
  locale: locale.value === 'de' ? deLocale : 'en',
  colorScheme: isDark.value ? 'dark' : 'light',
  firstDay: 1,
  height: '100%',
  weekNumbers: true,
  nowIndicator: true,
  dayMaxEvents: 4,
  slotMinTime: '06:00:00',
  slotMaxTime: '20:00:00',
  eventTimeFormat: { hour: '2-digit', minute: '2-digit', hour12: false },
  events: fetchEvents,
  datesSet: (info) => (title.value = info.view.title),
  eventClick: (info) => open(info.event.extendedProps.entry as CalendarEntry),
}))

watch(view, (name) => api()?.changeView(name))
watch(enabled, () => api()?.refetchEvents(), { deep: true })

function toggle(kind: CalendarKind) {
  enabled.value = enabled.value.includes(kind)
    ? enabled.value.filter((k) => k !== kind)
    : [...enabled.value, kind]
}

const legend = computed(() =>
  CALENDAR_KINDS.map((kind) => ({ kind, icon: KIND_ICONS[kind], color: kindColor(kind) })),
)
</script>

<template>
  <div class="page calendar-page">
    <PageHeader :title="t('calendar.title')" :subtitle="t('calendar.subtitle')" />

    <div class="toolbar">
      <NButtonGroup size="small">
        <NButton :title="t('calendar.previous')" @click="api()?.prev()">
          <template #icon><ChevronLeft :size="16" /></template>
        </NButton>
        <NButton @click="api()?.today()">{{ t('common.today') }}</NButton>
        <NButton :title="t('calendar.next')" @click="api()?.next()">
          <template #icon><ChevronRight :size="16" /></template>
        </NButton>
      </NButtonGroup>
      <h2 class="title">{{ title }}</h2>
      <span v-if="loading" class="mono muted small">…</span>
      <div class="grow" />
      <NRadioGroup v-model:value="view" size="small">
        <NRadioButton value="dayGridMonth">{{ t('calendar.views.month') }}</NRadioButton>
        <NRadioButton value="timeGridWeek">{{ t('calendar.views.week') }}</NRadioButton>
        <NRadioButton value="listMonth">{{ t('calendar.views.list') }}</NRadioButton>
      </NRadioGroup>
    </div>

    <div class="filters" role="group" :aria-label="t('common.filters')">
      <button
        v-for="item in legend"
        :key="item.kind"
        type="button"
        class="chip"
        :class="{ off: !enabled.includes(item.kind) }"
        :style="{ '--kind': item.color }"
        :aria-pressed="enabled.includes(item.kind)"
        @click="toggle(item.kind)"
      >
        <component :is="item.icon" :size="14" />
        {{ t(`calendar.kinds.${item.kind}`) }}
      </button>
      <span class="legend muted small">
        <span class="swatch filled" />{{ t('calendar.legend.confirmed') }}
        <span class="swatch outline" />{{ t('calendar.legend.tentative') }}
        <span class="swatch overdue" />{{ t('calendar.legend.overdue') }} <span class="sep">·</span
        >{{ t('calendar.permanentHidden') }}
      </span>
    </div>

    <div class="calendar-frame ar-calendar">
      <FullCalendar ref="calendar" :options="options">
        <template #eventContent="arg">
          <NTooltip placement="top-start" :show-arrow="false" :style="{ maxWidth: '340px' }">
            <template #trigger>
              <span class="event">
                <component
                  :is="KIND_ICONS[(arg.event.extendedProps.entry as CalendarEntry).kind]"
                  :size="12"
                />
                <b v-if="arg.timeText && !arg.event.allDay" class="mono">{{ arg.timeText }}</b>
                <span class="event-title">{{ arg.event.title }}</span>
              </span>
            </template>
            <div class="tip">
              <div class="eyebrow">
                {{ t(`calendar.kinds.${(arg.event.extendedProps.entry as CalendarEntry).kind}`) }}
                <template v-if="(arg.event.extendedProps.entry as CalendarEntry).kind === 'loan'">
                  ·
                  {{
                    enumLabel(
                      'reservationStatus',
                      (arg.event.extendedProps.entry as CalendarEntry).status,
                    )
                  }}
                </template>
              </div>
              <strong>{{ arg.event.title }}</strong>
              <div v-if="(arg.event.extendedProps.entry as CalendarEntry).overdue" class="overdue">
                {{
                  t('calendar.overdueSince', {
                    date: date(
                      (arg.event.extendedProps.entry as CalendarEntry).due ??
                        (arg.event.extendedProps.entry as CalendarEntry).start,
                    ),
                  })
                }}
              </div>
              <div
                v-for="line in (arg.event.extendedProps.entry as CalendarEntry).details"
                :key="line"
                class="mono line"
              >
                {{ line }}
              </div>
            </div>
          </NTooltip>
        </template>
      </FullCalendar>
    </div>
  </div>
</template>

<style scoped>
/* Exactly the content area's height: header and filters take what they need,
   the calendar fills the rest, so the page itself never scrolls. */
.calendar-page {
  display: flex;
  flex-direction: column;
  height: calc(100vh - var(--ar-header-height));
  max-width: none;
  padding-bottom: 20px;
}
.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  margin-bottom: 12px;
}
.title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  text-transform: capitalize;
}
.grow {
  flex: 1;
}
.small {
  font-size: 11.5px;
}
.filters {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 3px 10px;
  border: 1px solid color-mix(in srgb, var(--kind) 45%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--kind) 12%, transparent);
  color: var(--kind);
  font: inherit;
  font-size: 12px;
  font-weight: 500;
  cursor: pointer;
}
.chip.off {
  border-color: var(--ar-border);
  background: transparent;
  color: var(--ar-text-subtle);
}
.legend {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 6px;
  margin-left: 6px;
}
.swatch {
  width: 18px;
  height: 10px;
  margin-left: 8px;
  border-radius: 2px;
  border: 1.5px solid var(--ar-text-muted);
}
.swatch.filled {
  margin-left: 0;
  background: var(--ar-text-muted);
}
.swatch.outline {
  border-style: dashed;
}
.swatch.overdue {
  border-color: var(--ar-error);
  background: var(--ar-error);
}
.sep {
  margin: 0 4px;
}
.calendar-frame {
  flex: 1 1 auto;
  min-height: 480px;
  padding: 0;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  overflow: hidden;
}
.event {
  display: flex;
  align-items: center;
  gap: 4px;
  min-width: 0;
  overflow: hidden;
  white-space: nowrap;
  font-size: 11.5px;
}
.event-title {
  overflow: hidden;
  text-overflow: ellipsis;
}
.tip {
  display: grid;
  gap: 3px;
}
.line {
  font-size: 11.5px;
  color: var(--ar-text-muted);
}
.overdue {
  color: var(--ar-error);
  font-weight: 600;
}
</style>

<style>
/* FullCalendar "classic" theme driven by the Argus palette (light and dark). */
.ar-calendar {
  --fc-classic-primary: var(--ar-primary);
  --fc-classic-primary-foreground: var(--ar-on-primary);
  --fc-classic-event: var(--ar-primary);
  --fc-classic-event-contrast: var(--ar-on-primary);
  --fc-classic-highlight: var(--ar-primary-soft);
  --fc-classic-today: var(--ar-primary-soft);
  --fc-classic-now: var(--ar-error);
  --fc-classic-background: var(--ar-surface);
  --fc-classic-faint: var(--ar-surface-sunken);
  --fc-classic-muted: var(--ar-border);
  --fc-classic-strong: var(--ar-border-strong);
  --fc-classic-foreground: var(--ar-text);
  --fc-classic-faint-foreground: var(--ar-text-subtle);
  --fc-classic-muted-foreground: var(--ar-text-muted);
  --fc-classic-border: var(--ar-border);
  --fc-classic-strong-border: var(--ar-border-strong);
  --fc-classic-button: var(--ar-surface-raised);
  --fc-classic-button-border: var(--ar-border-strong);
  --fc-classic-button-strong: var(--ar-primary);
  --fc-classic-button-strong-border: var(--ar-primary);
  --fc-classic-button-outline: var(--ar-primary-soft);
  --fc-classic-button-foreground: var(--ar-text);
  --fc-classic-small-dot-width: 8px;
  --fc-classic-large-dot-width: 10px;
  --fc-classic-background-event: var(--ar-success);
  --fc-classic-background-event-opacity: 15%;
  --fc-classic-background-event-foreground-opacity: 50%;
  font-size: 12.5px;
}
/* Not confirmed yet (request awaiting approval, pickup not prepared): outline only. */
.ar-calendar .ar-tentative {
  /* FullCalendar sets the contrast colour inline; !important on a custom property wins over it. */
  --fc-event-contrast-color: var(--fc-event-color) !important;
  border: 1.5px dashed var(--fc-event-color) !important;
  background: color-mix(in srgb, var(--fc-event-color) 10%, transparent) !important;
  color: var(--fc-event-color) !important;
}
.ar-calendar .ar-tentative * {
  color: var(--fc-event-color) !important;
}
</style>
