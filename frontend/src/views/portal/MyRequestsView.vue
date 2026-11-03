<script setup lang="ts">
import { ChevronRight, PackageCheck, PackagePlus, Undo2 } from '@lucide/vue'
import { NButton, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import { isPast } from '@/utils/requests'

/**
 * The employee's requests: first what waits for them (devices to pick up, returns that
 * are overdue), then everything else in progress as a plain list, the closed ones folded
 * away below.
 */
const { t } = useI18n()
const { date, weekday } = useFormat()

const requests = ref<Schemas['AssetRequestListOut'][] | null>(null)
async function load() {
  const page = await requestsApi.list({ mine: true, page_size: 100, ordering: '-created_at' })
  requests.value = page.items
}
onMounted(load)
useLive(['request'], load)

type Request = Schemas['AssetRequestListOut']

/** In progress, in the order of what comes next for the employee. */
const RUNNING = ['ready', 'handed_out', 'confirmed', 'submitted', 'pending_approval'] as const
const rank = (r: Request) => RUNNING.indexOf(r.status as (typeof RUNNING)[number])

/** The employee has to act: pick up, or bring back what is overdue (overdue first). */
const needsAction = (r: Request) => r.status === 'ready' || r.is_overdue
const todo = computed(() =>
  (requests.value ?? [])
    .filter(needsAction)
    .sort((a, b) => Number(b.is_overdue) - Number(a.is_overdue)),
)
// Sorting is stable: within a status the newest stays first, as the API delivers them.
const running = computed(() =>
  (requests.value ?? [])
    .filter((r) => rank(r) >= 0 && !needsAction(r))
    .sort((a, b) => rank(a) - rank(b)),
)
const closed = computed(() => (requests.value ?? []).filter((r) => rank(r) < 0))
const showClosed = ref(false)

function period(r: Request): string {
  return `${date(r.start_date)} → ${r.end_date ? date(r.end_date) : t('common.permanent')}`
}

/** What there is to do, in one sentence: where and when to pick up, or since when overdue. */
function todoText(r: Request): string {
  if (r.is_overdue) return t('requests.mine.next.overdue', { date: date(r.end_date) })
  if (!r.pickup_at) return t('requests.mine.next.ready')
  return isPast(r.pickup_at)
    ? t('requests.mine.next.readyMissed', { date: weekday(r.pickup_at) })
    : t('requests.mine.next.readyAt', { date: weekday(r.pickup_at) })
}
</script>

<template>
  <div class="page">
    <PageHeader :title="t('requests.mine.title')" :subtitle="t('requests.mine.subtitle')">
      <template #actions>
        <RouterLink :to="{ name: 'portal-new' }">
          <NButton type="primary">
            <template #icon><PackagePlus :size="16" /></template>
            {{ t('nav.newRequest') }}
          </NButton>
        </RouterLink>
      </template>
    </PageHeader>

    <NSkeleton v-if="!requests" height="120px" :repeat="2" />
    <EmptyState v-else-if="!requests.length" :text="t('requests.mine.empty')" />
    <div v-else class="stack">
      <!-- What waits for the employee, set apart in the colour of what to do. -->
      <section v-if="todo.length">
        <h2 class="eyebrow section">{{ t('requests.mine.todo') }}</h2>
        <div class="list">
          <RouterLink
            v-for="r in todo"
            :key="r.id"
            :to="{ name: 'portal-request', params: { id: r.id } }"
            class="line todo"
            :class="r.is_overdue ? 'overdue' : 'ready'"
          >
            <span class="todo-icon">
              <component :is="r.is_overdue ? Undo2 : PackageCheck" :size="18" />
            </span>
            <span class="text">
              <span class="todo-head">
                <strong class="action">{{
                  r.is_overdue ? t('requests.mine.action.return') : t('requests.mine.action.pickup')
                }}</strong>
                <span class="title">{{ r.title }}</span>
              </span>
              <span class="todo-text">{{ todoText(r) }}</span>
              <span class="summary">{{ r.summary }}</span>
            </span>
            <ChevronRight :size="16" class="go" />
          </RouterLink>
        </div>
      </section>

      <section>
        <h2 class="eyebrow section">{{ t('requests.mine.active') }}</h2>
        <p v-if="!running.length" class="muted">
          {{ todo.length ? t('requests.mine.nothingElse') : t('requests.mine.noActive') }}
        </p>
        <div v-else class="list">
          <RouterLink
            v-for="r in running"
            :key="r.id"
            :to="{ name: 'portal-request', params: { id: r.id } }"
            class="line"
          >
            <span class="text">
              <strong class="title">{{ r.title }}</strong>
              <span class="summary">{{ r.summary }}</span>
            </span>
            <span class="meta">
              <StatusTag group="requestStatus" :value="r.status" />
              <span class="mono muted period">{{ period(r) }}</span>
            </span>
            <ChevronRight :size="16" class="go" />
          </RouterLink>
        </div>
      </section>

      <section v-if="closed.length">
        <button
          type="button"
          class="eyebrow section toggle"
          :aria-expanded="showClosed"
          @click="showClosed = !showClosed"
        >
          <ChevronRight :size="14" class="chevron" :class="{ open: showClosed }" />
          {{ t('requests.mine.closed') }}
          <span class="mono">{{ closed.length }}</span>
        </button>
        <div v-if="showClosed" class="list">
          <RouterLink
            v-for="r in closed"
            :key="r.id"
            :to="{ name: 'portal-request', params: { id: r.id } }"
            class="line closed-line"
          >
            <span class="text">
              <span class="title">{{ r.title }}</span>
            </span>
            <span class="meta">
              <StatusTag group="requestStatus" :value="r.status" />
              <span class="mono muted period">{{ period(r) }}</span>
            </span>
            <ChevronRight :size="16" class="go" />
          </RouterLink>
        </div>
      </section>
    </div>
  </div>
</template>

<style scoped>
.section {
  margin: 0 0 10px;
}
/* One framed list, a row per request. */
.list {
  display: grid;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
.line {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border-bottom: 1px solid var(--ar-border);
  color: inherit;
  text-decoration: none;
  transition: background-color 0.15s ease;
}
.line:last-child {
  border-bottom: none;
}
.line:hover {
  background: var(--ar-surface-sunken);
  text-decoration: none;
}
.text {
  display: grid;
  flex: 1;
  gap: 2px;
  min-width: 0;
}
.title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.summary {
  overflow: hidden;
  color: var(--ar-text-muted);
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.meta {
  display: flex;
  flex: none;
  align-items: center;
  gap: 14px;
}
.period {
  min-width: 190px;
  font-size: 12px;
  text-align: right;
}
.go {
  flex: none;
  color: var(--ar-text-subtle);
}
/* To do: the action in its colour, then what and when. */
.todo {
  --tone: var(--ar-success);
  border-left: 3px solid var(--tone);
}
.todo.overdue {
  --tone: var(--ar-error);
}
.todo-icon {
  display: grid;
  flex: none;
  place-items: center;
  width: 36px;
  height: 36px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--tone) 12%, transparent);
  color: var(--tone);
}
.todo-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  min-width: 0;
}
.action {
  flex: none;
  color: var(--tone);
}
.todo-text {
  font-size: 12.5px;
}
.closed-line .title {
  color: var(--ar-text-muted);
}
/* The closed ones fold away; the heading opens them. */
.toggle {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0;
  border: 0;
  background: none;
  font: inherit;
  letter-spacing: inherit;
  text-transform: inherit;
  cursor: pointer;
}
.toggle:hover {
  color: var(--ar-primary);
}
.chevron {
  transition: transform 0.15s ease;
}
.chevron.open {
  transform: rotate(90deg);
}
/* On a phone status and dates go below the title. */
@media (max-width: 760px) {
  .line {
    flex-wrap: wrap;
    row-gap: 8px;
  }
  .line .text {
    flex-basis: calc(100% - 40px);
  }
  .todo .text {
    flex-basis: calc(100% - 90px);
  }
  .meta {
    order: 3;
    width: 100%;
    justify-content: space-between;
  }
  .period {
    min-width: 0;
  }
}
</style>
