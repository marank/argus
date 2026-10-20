<script setup lang="ts">
import { NCard, NTimeline, NTimelineItem } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useFormat } from '@/composables/useFormat'
import type { Reservation, ReservationEvent, ReservationEventKind } from '@/types/reservations'

/** What happened to the request, newest first, as the backend recorded it. */
const props = defineProps<{ reservation: Reservation }>()
const { t } = useI18n()
const { date, dateTime, weekday, enumLabel } = useFormat()

type Tone = 'default' | 'info' | 'success' | 'warning' | 'error'
const TONES: Partial<Record<ReservationEventKind, Tone>> = {
  approved: 'success',
  declined: 'error',
  confirmed: 'info',
  rejected: 'error',
  ready: 'success',
  handed_out: 'info',
  extended: 'warning',
  reminded: 'warning',
  completed: 'success',
}

interface Entry {
  key: string
  at: string
  kind: ReservationEventKind
  by?: string
  items: string[]
  event: ReservationEvent
}

const MINUTE = 60_000
const closeInTime = (a: string, b: string) =>
  Math.abs(new Date(a).getTime() - new Date(b).getTime()) < MINUTE

/** Allocations made in one go (same person, same minute) read as one entry. */
const entries = computed<Entry[]>(() => {
  const list: Entry[] = []
  for (const event of props.reservation.events) {
    const last = list[list.length - 1]
    const by = event.actor?.display_name
    if (
      event.kind === 'allocated' &&
      last?.kind === 'allocated' &&
      last.by === by &&
      closeInTime(last.at, event.at)
    ) {
      last.items.push(...(event.data.items ?? []))
      continue
    }
    list.push({
      key: event.id,
      at: event.at,
      kind: event.kind,
      by,
      items: [...(event.data.items ?? [])],
      event,
    })
  }
  return list.reverse()
})

function title(entry: Entry): string {
  const key = `reservations.detail.event.${entry.kind}`
  return ['allocated', 'released'].includes(entry.kind)
    ? t(key, { count: entry.items.length }, entry.items.length)
    : t(key)
}

/** The details worth a line: who for, which devices, which dates, what was said. */
function details(entry: Entry): string[] {
  const d = entry.event.data
  const lines: string[] = []
  switch (entry.kind) {
    case 'created':
    case 'direct':
      if (d.requester) lines.push(t('reservations.detail.event.for', { name: d.requester }))
      if (d.follows) lines.push(t('reservations.again.follows') + ' ' + d.follows)
      break
    case 'assigned':
      lines.push(
        [d.team, d.assignee].filter(Boolean).join(' · ') || t('reservations.detail.event.nobody'),
      )
      break
    case 'ready':
    case 'rescheduled':
      lines.push(
        [
          d.handover_mode ? t(`handover.mode.${d.handover_mode}`) : '',
          d.pickup_at ? weekday(d.pickup_at) : '',
          d.pickup_location ?? '',
        ]
          .filter(Boolean)
          .join(' · '),
      )
      break
    case 'handed_out':
      lines.push(
        [
          d.method ? enumLabel('handoverMethod', d.method) : '',
          d.received_by ? `${t('handover.receivedBy')}: ${d.received_by}` : '',
          d.location ?? '',
        ]
          .filter(Boolean)
          .join(' · '),
      )
      break
    case 'extended':
      if (d.previous && d.end_date) lines.push(`${date(d.previous)} → ${date(d.end_date)}`)
      break
  }
  if (entry.items.length) lines.push(entry.items.join(', '))
  if (d.damaged?.length)
    lines.push(`${t('reservations.returning.damaged')}: ${d.damaged.join(', ')}`)
  if (d.comment) lines.push(d.comment)
  if (d.notes) lines.push(d.notes)
  return lines.filter(Boolean)
}
</script>

<template>
  <NCard :title="t('reservations.detail.history')" size="small">
    <NTimeline size="medium">
      <NTimelineItem
        v-for="entry in entries"
        :key="entry.key"
        :type="TONES[entry.kind] ?? 'default'"
        :time="dateTime(entry.at)"
      >
        <template #header>
          <strong>{{ title(entry) }}</strong>
          <span v-if="entry.by" class="muted by"> · {{ entry.by }}</span>
        </template>
        <div v-for="(line, index) in details(entry)" :key="index" class="detail">
          {{ line }}
        </div>
      </NTimelineItem>
    </NTimeline>
  </NCard>
</template>

<style scoped>
.by {
  font-weight: 400;
}
.detail {
  font-size: 12.5px;
  white-space: pre-line;
  overflow-wrap: anywhere;
}
</style>
