<script setup lang="ts">
import { NCard, NCheckbox, NCheckboxGroup, NSkeleton, NSwitch } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { calendarApi } from '@/api/calendar'
import {
  entryColor,
  entryLabel,
  entryRoute,
  KIND_ICONS,
  kindColor,
} from '@/components/calendar/kinds'
import { toIsoDate, useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import type { CalendarEntry, CalendarKind } from '@/types/calendar'
import type { WidgetProps } from '@/types/dashboard'

import { isBoolean, someOf, useOption } from './options'
import WidgetOptions from './WidgetOptions.vue'

const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

/** Lending periods span days and would fill every column; the dates that need action stay. */
const KINDS: CalendarKind[] = ['pickup', 'return', 'delivery', 'warranty', 'license']

const { t } = useI18n()
const { weekday } = useFormat()
const stored = () => props.options
const save = (options: Record<string, unknown>) => emit('update:options', options)
const kinds = useOption<CalendarKind[]>(stored, save, 'kinds', KINDS, someOf(KINDS))
const hideEmpty = useOption(stored, save, 'hide_empty', false, isBoolean)
const entries = ref<CalendarEntry[] | null>(null)

const days = Array.from({ length: 7 }, (_, i) => {
  const day = new Date()
  day.setDate(day.getDate() + i)
  return toIsoDate(day)!
})

const load = async () => (entries.value = await calendarApi.entries(days[0]!, days[6]!, KINDS))
onMounted(load)
useLive(['request', 'order', 'asset', 'license'], load)

/** All kinds are loaded once; switching one off only filters. */
const shown = computed(() => (entries.value ?? []).filter((e) => kinds.value.includes(e.kind)))

const byDay = computed(() =>
  days
    .map((day, index) => ({
      day,
      name:
        index === 0
          ? t('dashboard.widgets.week.today')
          : index === 1
            ? t('dashboard.widgets.week.tomorrow')
            : weekday(day),
      entries: shown.value.filter((e) => e.start.slice(0, 10) === day),
    }))
    .filter((d) => !hideEmpty.value || d.entries.length),
)
</script>

<template>
  <NCard :title="title ?? t('dashboard.widgets.week.title')" size="small">
    <template #header-extra>
      <RouterLink :to="{ name: 'calendar' }" class="muted">{{ t('nav.calendar') }}</RouterLink>
      <WidgetOptions>
        <div>
          <span class="eyebrow">{{ t('dashboard.widgets.week.kinds') }}</span>
          <NCheckboxGroup v-model:value="kinds">
            <div class="kinds">
              <NCheckbox v-for="kind in KINDS" :key="kind" :value="kind">
                <span class="kind" :style="{ '--tone': kindColor(kind) }">
                  <component :is="KIND_ICONS[kind]" :size="13" />
                  {{ t(`calendar.kinds.${kind}`) }}
                </span>
              </NCheckbox>
            </div>
          </NCheckboxGroup>
        </div>
        <label class="switch">
          <NSwitch v-model:value="hideEmpty" size="small" />
          {{ t('dashboard.widgets.week.hideEmpty') }}
        </label>
      </WidgetOptions>
    </template>
    <NSkeleton v-if="!entries" text :repeat="3" />
    <p v-else-if="!shown.length" class="muted">{{ t('dashboard.widgets.week.empty') }}</p>
    <div v-else class="week" :style="{ '--days': byDay.length }">
      <section v-for="d in byDay" :key="d.day" class="day" :class="{ empty: !d.entries.length }">
        <header class="eyebrow">{{ d.name }}</header>
        <p v-if="!d.entries.length" class="muted">—</p>
        <component
          :is="entryRoute(entry) ? 'RouterLink' : 'div'"
          v-for="entry in d.entries"
          :key="entry.id"
          :to="entryRoute(entry) ?? undefined"
          class="entry"
          :style="{ '--tone': entryColor(entry) }"
        >
          <component :is="KIND_ICONS[entry.kind]" :size="13" />
          <span>{{ entryLabel(entry, t) }}</span>
        </component>
      </section>
    </div>
  </NCard>
</template>

<style scoped>
.kinds {
  display: grid;
  gap: 6px;
}
.kind {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.kind svg {
  color: var(--tone);
}
.switch {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.week {
  display: grid;
  grid-template-columns: repeat(var(--days), minmax(0, 1fr));
  gap: 10px;
}
.day {
  display: grid;
  align-content: start;
  gap: 4px;
  min-width: 0;
}
.day p {
  margin: 0;
}
.entry {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 4px 6px;
  border-left: 3px solid var(--tone);
  border-radius: 2px;
  background: color-mix(in srgb, var(--tone) 10%, transparent);
  color: inherit;
  font-size: 12px;
  line-height: 1.35;
  text-decoration: none;
}
.entry svg {
  flex: none;
  margin-top: 2px;
  color: var(--tone);
}
.entry span {
  min-width: 0;
  overflow-wrap: anywhere;
}
a.entry:hover {
  background: color-mix(in srgb, var(--tone) 20%, transparent);
}
/* Not enough room for seven columns: the days one below the other, empty ones left out. */
@container (max-width: 760px) {
  .week {
    grid-template-columns: minmax(0, 1fr);
  }
  .day.empty {
    display: none;
  }
}
</style>
