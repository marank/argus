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

type Schedule = Schemas['ScheduleEventOut']['data']

const compact = (lines: (string | null | undefined)[]) =>
  lines.filter((line): line is string => !!line)

/** "Label: a, b" for a non-empty list, else nothing. */
const listLine = (key: string, values: string[]) =>
  values.length ? `${t(key)}: ${values.join(', ')}` : null

/** How and where the devices are handed over, for a ready or rescheduled step. */
const scheduleLine = (d: Schedule) =>
  joined([
    d.handover_mode && t(`handover.mode.${d.handover_mode}`),
    d.pickup_at && weekday(d.pickup_at),
    d.pickup_location,
    d.notified === false && t('handover.notNotified'),
  ])

/** Prepared by more than the person who finished it: who allocated what. */
function allocationLines(d: Schedule): (string | null)[] {
  const key = d.items.length ? 'allocatedBy' : 'addedBy'
  return [
    ...d.allocated_by.map(
      (group) =>
        `${t(`requests.detail.event.${key}`, { name: group.name || '?' })}: ${group.items.join(', ')}`,
    ),
    listLine('requests.detail.event.removed', d.removed),
  ]
}

/** What the step itself says, by kind. */
function kindLines(event: Event): (string | null)[] {
  switch (event.kind) {
    case 'created':
    case 'direct':
    case 'quick':
      return [
        event.data.requester && t('requests.detail.event.for', { name: event.data.requester }),
        event.data.follows && t('requests.again.follows') + ' ' + event.data.follows,
      ]
    case 'approved':
    case 'declined':
    case 'confirmed':
    case 'rejected':
      return [event.data.comment]
    case 'assigned':
      return [joined([event.data.team, event.data.assignee]) || t('requests.detail.event.nobody')]
    case 'ready':
    case 'rescheduled':
      // Ready again after a change: only what changed (the first time lists everything).
      return [
        scheduleLine(event.data),
        listLine('requests.detail.event.added', event.data.added),
        listLine('requests.detail.event.removed', event.data.removed),
      ]
    case 'handed_out':
      return [
        joined([
          event.data.method && enumLabel('handoverMethod', event.data.method),
          event.data.received_by && `${t('handover.receivedBy')}: ${event.data.received_by}`,
          event.data.location,
        ]),
      ]
    case 'extended':
      return [
        event.data.previous && event.data.end_date
          ? `${date(event.data.previous)} → ${date(event.data.end_date)}`
          : null,
      ]
    case 'replaced':
      return [event.data.by && t('requests.replace.by', { number: event.data.by })]
    case 'allocated':
    case 'released':
    case 'reopened':
    case 'reminded':
    case 'returned':
    case 'cancelled':
    case 'completed':
      return []
  }
}

/** The details worth a line: who for, which devices, which dates, what was said. */
function details(entry: Entry): string[] {
  const event = entry.event
  if (
    (event.kind === 'ready' || event.kind === 'rescheduled') &&
    byOthers(entry, event.data.allocated_by)
  )
    return compact([scheduleLine(event.data), ...allocationLines(event.data)])
  const lines = kindLines(event)
  if (entry.items.length) lines.push(entry.items.join(', '))
  // Handed out or taken back outside the system: the lines without a recorded device.
  if (event.kind === 'handed_out' || event.kind === 'returned')
    lines.push(listLine('requests.detail.event.withoutDevices', event.data.missing))
  if (event.kind === 'returned')
    lines.push(listLine('requests.returning.damaged', event.data.damaged), event.data.notes)
  return compact(lines)
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
