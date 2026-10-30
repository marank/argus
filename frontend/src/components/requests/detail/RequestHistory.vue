<script setup lang="ts">
import { NCard, NTimeline, NTimelineItem } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import { useFormat } from '@/composables/useFormat'

/** What happened to the request, newest first, as the backend recorded it. */
const props = defineProps<{ assetRequest: Schemas['AssetRequestOut'] }>()
const { t } = useI18n()
const { date, dateTime, weekday, enumLabel } = useFormat()

type Tone = 'default' | 'info' | 'success' | 'warning' | 'error'
const TONES: Partial<Record<Schemas['AssetRequestEventKind'], Tone>> = {
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
  kind: Schemas['AssetRequestEventKind']
  by?: string
  items: string[]
  event: Schemas['AssetRequestEventOut']
}

/** `data` is free-form: the plain texts and lists of texts the workflow recorded. */
const text = (value: unknown) => (typeof value === 'string' ? value : '')
const texts = (value: unknown) =>
  Array.isArray(value) ? value.filter((v): v is string => typeof v === 'string') : []

const MINUTE = 60_000
const closeInTime = (a: string, b: string) =>
  Math.abs(new Date(a).getTime() - new Date(b).getTime()) < MINUTE

/** Allocations made in one go (same person, same minute) read as one entry. */
const entries = computed<Entry[]>(() => {
  const list: Entry[] = []
  for (const event of props.assetRequest.events) {
    const last = list[list.length - 1]
    const by = event.actor?.display_name
    if (
      event.kind === 'allocated' &&
      last?.kind === 'allocated' &&
      last.by === by &&
      closeInTime(last.at, event.at)
    ) {
      last.items.push(...texts(event.data.items))
      continue
    }
    list.push({
      key: event.id,
      at: event.at,
      kind: event.kind,
      by,
      items: texts(event.data.items),
      event,
    })
  }
  return list.reverse()
})

function title(entry: Entry): string {
  const key = `requests.detail.event.${entry.kind}`
  return ['allocated', 'released'].includes(entry.kind)
    ? t(key, { count: entry.items.length }, entry.items.length)
    : t(key)
}

/** The details worth a line: who for, which devices, which dates, what was said. */
function details(entry: Entry): string[] {
  const d = entry.event.data
  const added = texts(d.added)
  const removed = texts(d.removed)
  const damaged = texts(d.damaged)
  const lines: string[] = []
  switch (entry.kind) {
    case 'created':
    case 'direct':
    case 'quick':
      if (d.requester) lines.push(t('requests.detail.event.for', { name: text(d.requester) }))
      if (d.follows) lines.push(t('requests.again.follows') + ' ' + text(d.follows))
      break
    case 'assigned':
      lines.push(
        [text(d.team), text(d.assignee)].filter(Boolean).join(' · ') ||
          t('requests.detail.event.nobody'),
      )
      break
    case 'ready':
    case 'rescheduled':
      lines.push(
        [
          d.handover_mode ? t(`handover.mode.${text(d.handover_mode)}`) : '',
          d.pickup_at ? weekday(text(d.pickup_at)) : '',
          text(d.pickup_location),
          d.notified === false ? t('handover.notNotified') : '',
        ]
          .filter(Boolean)
          .join(' · '),
      )
      // Ready again after a change: only what changed (the first time lists everything).
      if (added.length) lines.push(`${t('assetRequests.detail.event.added')}: ${added.join(', ')}`)
      if (removed.length)
        lines.push(`${t('assetRequests.detail.event.removed')}: ${removed.join(', ')}`)
      break
    case 'handed_out':
      lines.push(
        [
          d.method ? enumLabel('handoverMethod', text(d.method)) : '',
          d.received_by ? `${t('handover.receivedBy')}: ${text(d.received_by)}` : '',
          text(d.location),
        ]
          .filter(Boolean)
          .join(' · '),
      )
      break
    case 'extended':
      if (d.previous && d.end_date)
        lines.push(`${date(text(d.previous))} → ${date(text(d.end_date))}`)
      break
  }
  if (entry.items.length) lines.push(entry.items.join(', '))
  if (damaged.length) lines.push(`${t('assetRequests.returning.damaged')}: ${damaged.join(', ')}`)
  lines.push(text(d.comment), text(d.notes))
  return lines.filter(Boolean)
}
</script>

<template>
  <NCard :title="t('requests.detail.history')" size="small">
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
