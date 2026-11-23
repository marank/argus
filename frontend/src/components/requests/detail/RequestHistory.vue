<script setup lang="ts">
import { NCard, NTimeline, NTimelineItem } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import type { Schemas } from '@/api/types'
import { useFormat } from '@/composables/useFormat'

/**
 * What happened to the request, newest first, as the backend recorded it. For IT,
 * `activityLink` links the activity log of the request: every allocation and removal, with who did it.
 */
const props = defineProps<{ assetRequest: Schemas['AssetRequestOut']; activityLink?: boolean }>()
const { t } = useI18n()
const { date, dateTime, weekday, enumLabel } = useFormat()

type Event = Schemas['AssetRequestEventOut']
type Kind = Event['kind']

type Tone = 'default' | 'info' | 'success' | 'warning' | 'error'
const TONES: Partial<Record<Kind, Tone>> = {
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
  by?: string
  items: string[]
  event: Event
}

/** The devices a step names, for the kinds that note any. */
const itemsOf = (event: Event): string[] => ('items' in event.data ? event.data.items : [])

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
      last?.event.kind === 'allocated' &&
      last.by === by &&
      closeInTime(last.at, event.at)
    ) {
      last.items.push(...itemsOf(event))
      continue
    }
    list.push({ key: event.id, at: event.at, by, items: itemsOf(event), event })
  }
  return list.reverse()
})

function title(entry: Entry): string {
  const kind = entry.event.kind
  const key = `requests.detail.event.${kind}`
  return kind === 'allocated' || kind === 'released'
    ? t(key, { count: entry.items.length }, entry.items.length)
    : t(key)
}

const joined = (parts: (string | null | false)[]) => parts.filter(Boolean).join(' · ')

/** Someone other than who finished the preparation allocated part of it. */
const byOthers = (entry: Entry, groups: { name?: string }[]) =>
  groups.some((group) => (group.name || undefined) !== entry.by)

/** The details worth a line: who for, which devices, which dates, what was said. */
// eslint-disable-next-line complexity -- one case per event kind, each a few optional parts
function details(entry: Entry): string[] {
  const event = entry.event
  const lines: (string | null)[] = []
  switch (event.kind) {
    case 'created':
    case 'direct':
    case 'quick':
      if (event.data.requester)
        lines.push(t('requests.detail.event.for', { name: event.data.requester }))
      if (event.data.follows) lines.push(t('requests.again.follows') + ' ' + event.data.follows)
      break
    case 'approved':
    case 'declined':
    case 'confirmed':
    case 'rejected':
      lines.push(event.data.comment)
      break
    case 'assigned':
      lines.push(
        joined([event.data.team, event.data.assignee]) || t('requests.detail.event.nobody'),
      )
      break
    case 'ready':
    case 'rescheduled': {
      const d = event.data
      lines.push(
        joined([
          d.handover_mode && t(`handover.mode.${d.handover_mode}`),
          d.pickup_at && weekday(d.pickup_at),
          d.pickup_location,
          d.notified === false && t('handover.notNotified'),
        ]),
      )
      if (byOthers(entry, d.allocated_by)) {
        // Prepared by more than the person who finished it: who allocated what.
        const key = d.items.length ? 'allocatedBy' : 'addedBy'
        for (const group of d.allocated_by)
          lines.push(
            `${t(`requests.detail.event.${key}`, { name: group.name || '?' })}: ${group.items.join(', ')}`,
          )
        if (d.removed.length)
          lines.push(`${t('requests.detail.event.removed')}: ${d.removed.join(', ')}`)
        return lines.filter((line): line is string => !!line)
      }
      // Ready again after a change: only what changed (the first time lists everything).
      if (d.added.length) lines.push(`${t('requests.detail.event.added')}: ${d.added.join(', ')}`)
      if (d.removed.length)
        lines.push(`${t('requests.detail.event.removed')}: ${d.removed.join(', ')}`)
      break
    }
    case 'handed_out':
      lines.push(
        joined([
          event.data.method && enumLabel('handoverMethod', event.data.method),
          event.data.received_by && `${t('handover.receivedBy')}: ${event.data.received_by}`,
          event.data.location,
        ]),
      )
      break
    case 'extended':
      if (event.data.previous && event.data.end_date)
        lines.push(`${date(event.data.previous)} → ${date(event.data.end_date)}`)
      break
    case 'replaced':
      if (event.data.by) lines.push(t('requests.replace.by', { number: event.data.by }))
      break
  }
  if (entry.items.length) lines.push(entry.items.join(', '))
  // Handed out or taken back outside the system: the lines without a recorded device.
  if ((event.kind === 'handed_out' || event.kind === 'returned') && event.data.missing.length)
    lines.push(`${t('requests.detail.event.withoutDevices')}: ${event.data.missing.join(', ')}`)
  if (event.kind === 'returned') {
    if (event.data.damaged.length)
      lines.push(`${t('requests.returning.damaged')}: ${event.data.damaged.join(', ')}`)
    lines.push(event.data.notes)
  }
  return lines.filter((line): line is string => !!line)
}
</script>

<template>
  <NCard :title="t('requests.detail.history')" size="small">
    <template v-if="activityLink" #header-extra>
      <RouterLink
        :to="{ name: 'activities', query: { subject: assetRequest.id } }"
        class="activity-link"
      >
        {{ t('requests.detail.activityLog') }}
      </RouterLink>
    </template>
    <NTimeline size="medium">
      <NTimelineItem
        v-for="entry in entries"
        :key="entry.key"
        :type="TONES[entry.event.kind] ?? 'default'"
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
.activity-link {
  font-size: 12.5px;
}
.by {
  font-weight: 400;
}
.detail {
  font-size: 12.5px;
  white-space: pre-line;
  overflow-wrap: anywhere;
}
</style>
