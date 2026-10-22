<script setup lang="ts">
import { NCard, NTimeline, NTimelineItem } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import { useFormat } from '@/composables/useFormat'
import type { AssetRequest, AssetRequestEvent, AssetRequestEventKind } from '@/types/requests'

/** What happened to the request, newest first, as the backend recorded it. */
const props = defineProps<{ assetRequest: AssetRequest }>()
const { t } = useI18n()
const { date, dateTime, weekday, enumLabel } = useFormat()

type Tone = 'default' | 'info' | 'success' | 'warning' | 'error'
const TONES: Partial<Record<AssetRequestEventKind, Tone>> = {
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
  kind: AssetRequestEventKind
  by?: string
  items: string[]
  event: AssetRequestEvent
}

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
  const key = `requests.detail.event.${entry.kind}`
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
    case 'quick':
      if (d.requester) lines.push(t('requests.detail.event.for', { name: d.requester }))
      if (d.follows) lines.push(t('requests.again.follows') + ' ' + d.follows)
      break
    case 'assigned':
      lines.push(
        [d.team, d.assignee].filter(Boolean).join(' · ') || t('requests.detail.event.nobody'),
      )
      break
    case 'ready':
    case 'rescheduled':
      lines.push(
        [
          d.handover_mode ? t(`handover.mode.${d.handover_mode}`) : '',
          d.pickup_at ? weekday(d.pickup_at) : '',
          d.pickup_location ?? '',
          d.notified === false ? t('handover.notNotified') : '',
        ]
          .filter(Boolean)
          .join(' · '),
      )
      // Ready again after a change: only what changed (the first time lists everything).
      if (d.added?.length)
        lines.push(`${t('assetRequests.detail.event.added')}: ${d.added.join(', ')}`)
      if (d.removed?.length)
        lines.push(`${t('assetRequests.detail.event.removed')}: ${d.removed.join(', ')}`)
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
    lines.push(`${t('assetRequests.returning.damaged')}: ${d.damaged.join(', ')}`)
  if (d.comment) lines.push(d.comment)
  if (d.notes) lines.push(d.notes)
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
