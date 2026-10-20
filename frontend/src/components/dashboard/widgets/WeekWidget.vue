<script setup lang="ts">
import { NCard, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { calendarApi } from '@/api/calendar'
import { entryColor, entryLabel, entryRoute, KIND_ICONS } from '@/components/calendar/kinds'
import { toIsoDate, useFormat } from '@/composables/useFormat'
import type { CalendarEntry, CalendarKind } from '@/types/calendar'
import type { WidgetProps } from '@/types/dashboard'

defineProps<WidgetProps>()

/** Lending periods span days and would fill every column; the dates that need action stay. */
const KINDS: CalendarKind[] = ['pickup', 'return', 'delivery', 'warranty', 'license']

const { t } = useI18n()
const { weekday } = useFormat()
const entries = ref<CalendarEntry[] | null>(null)

const days = Array.from({ length: 7 }, (_, i) => {
  const day = new Date()
  day.setDate(day.getDate() + i)
  return toIsoDate(day)!
})

onMounted(async () => {
  entries.value = await calendarApi.entries(days[0]!, days[6]!, KINDS)
})

const byDay = computed(() =>
  days.map((day, index) => ({
    day,
    name:
      index === 0
        ? t('dashboard.widgets.week.today')
        : index === 1
          ? t('dashboard.widgets.week.tomorrow')
          : weekday(day),
    entries: (entries.value ?? []).filter((e) => e.start.slice(0, 10) === day),
  })),
)
</script>

<template>
  <NCard :title="t('dashboard.widgets.week.title')" size="small">
    <template #header-extra>
      <RouterLink :to="{ name: 'calendar' }" class="muted">{{ t('nav.calendar') }}</RouterLink>
    </template>
    <NSkeleton v-if="!entries" text :repeat="3" />
    <p v-else-if="!entries.length" class="muted">{{ t('dashboard.widgets.week.empty') }}</p>
    <div v-else class="week">
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
.week {
  display: grid;
  grid-template-columns: repeat(7, minmax(0, 1fr));
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
