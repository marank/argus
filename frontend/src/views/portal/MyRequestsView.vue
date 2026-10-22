<script setup lang="ts">
import { ChevronRight, PackagePlus } from '@lucide/vue'
import { useStorage } from '@vueuse/core'
import { NButton, NRadioButton, NRadioGroup, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import type { AssetRequestListItem } from '@/types/requests'

/**
 * The employee's requests: running ones as cards with progress and what happens
 * next (one row per status, or newest first), closed ones as a compact list below.
 */
const { t } = useI18n()
const { date, weekday, enumLabel } = useFormat()
const sortBy = useStorage<'status' | 'date'>('argus.my-requests-sort', 'status')

const requests = ref<AssetRequestListItem[] | null>(null)
async function load() {
  const page = await requestsApi.list({ mine: true, page_size: 100, ordering: '-created_at' })
  requests.value = page.items
}
onMounted(load)
useLive(['request'], load)

const STEPS = ['submitted', 'confirmed', 'ready', 'handed_out'] as const
// Waiting for the department comes before the first step.
const ACTIVE = new Set<string>(['pending_approval', ...STEPS])

const active = computed(() => (requests.value ?? []).filter((r) => ACTIVE.has(r.status)))
const closed = computed(() => (requests.value ?? []).filter((r) => !ACTIVE.has(r.status)))

/** Rows of cards: per status with the most urgent first, or one row by date. */
const STATUS_ROWS = ['ready', 'handed_out', 'confirmed', 'submitted', 'pending_approval'] as const
const rows = computed(() => {
  if (sortBy.value === 'date') return [{ key: 'all', label: '', items: active.value }]
  return STATUS_ROWS.map((status) => ({
    key: status,
    label: enumLabel('requestStatus', status),
    items: active.value.filter((r) => r.status === status),
  })).filter((row) => row.items.length)
})

const stepIndex = (r: AssetRequestListItem) => STEPS.indexOf(r.status as (typeof STEPS)[number])

function period(r: AssetRequestListItem): string {
  return `${date(r.start_date)} → ${r.end_date ? date(r.end_date) : t('common.permanent')}`
}

/** One sentence on where the request stands and what the employee can expect. */
function nextStep(r: AssetRequestListItem): string {
  switch (r.status) {
    case 'pending_approval':
      return t('requests.mine.next.pending_approval')
    case 'submitted':
      return t('requests.mine.next.submitted')
    case 'confirmed':
      return t('requests.mine.next.confirmed')
    case 'ready':
      return r.pickup_at
        ? t('requests.mine.next.readyAt', { date: weekday(r.pickup_at) })
        : t('requests.mine.next.ready')
    default:
      if (r.is_overdue) return t('requests.mine.next.overdue', { date: date(r.end_date) })
      return r.end_date
        ? t('requests.mine.next.handedOut', { date: date(r.end_date) })
        : t('requests.mine.next.handedOutPermanent')
  }
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
      <section>
        <div class="section-head">
          <h2 class="eyebrow section">{{ t('requests.mine.active') }}</h2>
          <NRadioGroup v-model:value="sortBy" size="small" :aria-label="t('requests.mine.sortBy')">
            <NRadioButton value="status">{{ t('requests.mine.byStatus') }}</NRadioButton>
            <NRadioButton value="date">{{ t('requests.mine.byDate') }}</NRadioButton>
          </NRadioGroup>
        </div>
        <p v-if="!active.length" class="muted">{{ t('requests.mine.noActive') }}</p>
        <div v-for="row in rows" :key="row.key" class="row-block">
          <div v-if="row.label" class="row-label">
            {{ row.label }} <span class="mono muted">{{ row.items.length }}</span>
          </div>
          <div class="cards">
            <RouterLink
              v-for="r in row.items"
              :key="r.id"
              :to="{ name: 'portal-request', params: { id: r.id } }"
              class="card"
              :class="{ attention: r.status === 'ready', overdue: r.is_overdue }"
            >
              <div class="card-head">
                <div class="titles">
                  <strong>{{ r.title }}</strong>
                  <span class="mono muted small">{{ r.number }}</span>
                </div>
                <StatusTag group="requestStatus" :value="r.status" :pulse="r.status === 'ready'" />
              </div>
              <p class="summary small">{{ r.summary }}</p>
              <div class="progress" :aria-label="t('common.status')">
                <span
                  v-for="(step, index) in STEPS"
                  :key="step"
                  :class="{ done: index <= stepIndex(r) }"
                />
              </div>
              <div class="card-foot small">
                <span class="next">{{ nextStep(r) }}</span>
                <span class="mono muted">{{ period(r) }}</span>
              </div>
            </RouterLink>
          </div>
        </div>
      </section>

      <section v-if="closed.length">
        <h2 class="eyebrow section">{{ t('requests.mine.closed') }}</h2>
        <div class="closed">
          <RouterLink
            v-for="r in closed"
            :key="r.id"
            :to="{ name: 'portal-request', params: { id: r.id } }"
            class="closed-line"
          >
            <span class="mono muted">{{ r.number }}</span>
            <span class="title">{{ r.title }}</span>
            <span class="mono muted small">{{ period(r) }}</span>
            <StatusTag group="requestStatus" :value="r.status" />
            <ChevronRight :size="14" class="muted" />
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
.section-head .section {
  margin: 0;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}
.row-block + .row-block {
  margin-top: 16px;
}
.row-label {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 8px;
  font-size: 12.5px;
  font-weight: 600;
}
.small {
  font-size: 12px;
}
.cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 12px;
}
.card {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  color: inherit;
  text-decoration: none;
  transition: border-color 0.15s ease;
}
.card:hover {
  border-color: var(--ar-border-strong);
  text-decoration: none;
}
.card.attention {
  border-color: color-mix(in srgb, var(--ar-success) 45%, transparent);
}
.card.overdue {
  border-color: color-mix(in srgb, var(--ar-error) 45%, transparent);
}
.card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.titles {
  display: grid;
  min-width: 0;
}
.summary {
  margin: 0;
  color: var(--ar-text-muted);
}
/* Four segments: submitted, confirmed, ready, handed out. */
.progress {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 4px;
}
.progress span {
  height: 4px;
  border-radius: 2px;
  background: var(--ar-border);
  transition: background-color 0.3s ease;
}
.progress span.done {
  background: var(--ar-primary);
}
.attention .progress span.done {
  background: var(--ar-success);
}
.overdue .progress span.done {
  background: var(--ar-error);
}
.card-foot {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 4px 12px;
}
.next {
  font-weight: 500;
}
.overdue .next {
  color: var(--ar-error);
}
.closed {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto auto auto;
  column-gap: 14px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
.closed-line {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: subgrid;
  align-items: center;
  padding: 8px 12px;
  border-bottom: 1px solid var(--ar-border);
  color: inherit;
  text-decoration: none;
}
.closed-line:last-child {
  border-bottom: none;
}
.closed-line:hover {
  background: var(--ar-surface-sunken);
  text-decoration: none;
}
.title {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
