<script setup lang="ts">
import type { Schemas } from '@/api/types'
import {
  CalendarClock,
  ChevronRight,
  ClipboardCheck,
  Pencil,
  UserCheck,
  UserPlus,
  UserRound,
} from '@lucide/vue'
import { NButton, NSkeleton, NTag } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { delegationsApi } from '@/api/requests'
import PageHeader from '@/components/common/PageHeader.vue'
import DelegationFormModal from '@/components/portal/DelegationFormModal.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import { useAuthStore } from '@/stores/auth'

/**
 * Delegations of an approver: who decides in their place and when, whom the user stands in
 * for, and the delegations of the past.
 */
const { t } = useI18n()
const { date } = useFormat()
const auth = useAuthStore()
const confirm = useConfirm()
const { run } = useAction()

type Entry = Schemas['ApprovalDelegationOut']

const data = ref<Schemas['DelegationsOut'] | null>(null)
async function load() {
  data.value = await delegationsApi.list()
}
onMounted(load)

const canName = computed(() => !!auth.user?.is_department_approver)
const running = computed(() => data.value?.mine.filter((d) => d.status === 'running') ?? [])
const next = computed(() => data.value?.mine.find((d) => d.status === 'planned') ?? null)
const showPast = ref(false)

const period = (d: Entry) =>
  d.ends_on
    ? t('requests.delegations.period', { from: date(d.starts_on), until: date(d.ends_on) })
    : t('requests.delegations.periodOpen', { from: date(d.starts_on) })

const initials = (name: string) =>
  name
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

const STATUS_TYPE = { running: 'success', planned: 'info', ended: 'default' } as const

// The banner: who decides for the user right now, or what comes next.
const banner = computed(() => {
  if (running.value.length) {
    const names = running.value.map((d) => d.delegate.display_name).join(', ')
    const ends = running.value.map((d) => d.ends_on).filter((d): d is string => !!d)
    const until =
      ends.length === running.value.length
        ? t('requests.delegations.bannerUntil', { date: date(ends.sort().at(-1)) })
        : t('requests.delegations.bannerOpen')
    return {
      tone: 'running',
      title: t('requests.delegations.bannerRunning', { names }),
      text: until,
    }
  }
  if (next.value)
    return {
      tone: 'planned',
      title: t('requests.delegations.bannerPlanned', { name: next.value.delegate.display_name }),
      text: period(next.value),
    }
  return {
    tone: 'none',
    title: t('requests.delegations.bannerNone'),
    text: t('requests.delegations.bannerNoneText'),
  }
})

// Adding or changing.
const showForm = ref(false)
const editing = ref<Entry | null>(null)
function add() {
  editing.value = null
  showForm.value = true
}
function edit(d: Entry) {
  editing.value = d
  showForm.value = true
}

async function endNow(d: Entry) {
  const question =
    d.status === 'running'
      ? t('requests.delegations.confirmEnd', { name: d.delegate.display_name })
      : t('requests.delegations.confirmRemove', { name: d.delegate.display_name })
  if (!(await confirm(question))) return
  await run(() => delegationsApi.end(d.id))
  await load()
}

async function backNow() {
  if (!(await confirm(t('requests.delegations.confirmBack')))) return
  await run(() => Promise.all(running.value.map((d) => delegationsApi.end(d.id))))
  await load()
}
</script>

<template>
  <div class="page narrow">
    <PageHeader
      :title="t('requests.delegations.title')"
      :subtitle="t('requests.delegations.subtitle')"
    >
      <template v-if="canName" #actions>
        <NButton type="primary" @click="add">
          <template #icon><UserPlus :size="16" /></template>
          {{ t('requests.delegations.add') }}
        </NButton>
      </template>
    </PageHeader>

    <NSkeleton v-if="!data" height="120px" :repeat="2" />
    <div v-else class="stack">
      <!-- Whether someone decides for the user right now. -->
      <section v-if="canName" class="banner" :class="banner.tone">
        <span class="banner-icon">
          <component :is="banner.tone === 'none' ? UserRound : UserCheck" :size="20" />
        </span>
        <span class="banner-text">
          <strong>{{ banner.title }}</strong>
          <span>{{ banner.text }}</span>
          <span v-if="data.departments.length" class="departments">
            {{ t('requests.delegations.departments') }}
            <NTag
              v-for="department in data.departments"
              :key="department.id"
              size="small"
              :bordered="false"
            >
              {{ department.name }}
            </NTag>
          </span>
        </span>
        <NButton v-if="running.length" secondary @click="backNow">
          {{ t('requests.delegations.back') }}
        </NButton>
      </section>

      <section v-if="data.received.length">
        <h2 class="eyebrow section">{{ t('requests.delegations.receivedTitle') }}</h2>
        <div class="list">
          <div v-for="d in data.received" :key="d.id" class="line">
            <span class="avatar mono">{{ initials(d.approver.display_name) }}</span>
            <span class="text">
              <strong>{{ d.approver.display_name }}</strong>
              <span class="muted small">{{
                t(`requests.delegations.receivedText.${d.status}`)
              }}</span>
            </span>
            <span class="meta">
              <NTag size="small" :bordered="false" :type="STATUS_TYPE[d.status]">
                {{ t(`requests.delegations.status.${d.status}`) }}
              </NTag>
              <span class="mono muted period">{{ period(d) }}</span>
            </span>
          </div>
        </div>
        <RouterLink :to="{ name: 'portal-approvals' }" class="to-approvals">
          <ClipboardCheck :size="14" />
          {{ t('requests.delegations.toApprovals') }}
          <ChevronRight :size="14" />
        </RouterLink>
      </section>

      <section v-if="canName">
        <h2 class="eyebrow section">{{ t('requests.delegations.mineTitle') }}</h2>
        <div v-if="!data.mine.length" class="empty">
          <CalendarClock :size="20" />
          <p>{{ t('requests.delegations.none') }}</p>
          <NButton size="small" secondary @click="add">
            <template #icon><UserPlus :size="14" /></template>
            {{ t('requests.delegations.add') }}
          </NButton>
        </div>
        <div v-else class="list">
          <div v-for="d in data.mine" :key="d.id" class="line" :class="d.status">
            <span class="avatar mono">{{ initials(d.delegate.display_name) }}</span>
            <span class="text">
              <strong>{{ d.delegate.display_name }}</strong>
              <span class="mono muted small">{{ d.delegate.username }}</span>
            </span>
            <span class="meta">
              <NTag size="small" :bordered="false" :type="STATUS_TYPE[d.status]">
                {{ t(`requests.delegations.status.${d.status}`) }}
              </NTag>
              <span class="mono muted period">{{ period(d) }}</span>
            </span>
            <span class="actions">
              <NButton size="small" quaternary @click="edit(d)">
                <template #icon><Pencil :size="14" /></template>
                {{ t('requests.delegations.changePeriod') }}
              </NButton>
              <NButton size="small" quaternary type="error" @click="endNow(d)">
                {{
                  d.status === 'running'
                    ? t('requests.delegations.end')
                    : t('requests.delegations.remove')
                }}
              </NButton>
            </span>
          </div>
        </div>
      </section>

      <section v-if="canName && data.past.length">
        <button
          type="button"
          class="eyebrow section toggle"
          :aria-expanded="showPast"
          @click="showPast = !showPast"
        >
          <ChevronRight :size="14" class="chevron" :class="{ open: showPast }" />
          {{ t('requests.delegations.pastTitle') }}
          <span class="mono">{{ data.past.length }}</span>
        </button>
        <div v-if="showPast" class="list">
          <div v-for="d in data.past" :key="d.id" class="line ended">
            <span class="avatar mono">{{ initials(d.delegate.display_name) }}</span>
            <span class="text">
              <span>{{ d.delegate.display_name }}</span>
            </span>
            <span class="meta">
              <span class="mono muted period">{{ period(d) }}</span>
            </span>
          </div>
        </div>
      </section>

      <section class="how">
        <h2 class="eyebrow section">{{ t('requests.delegations.howTitle') }}</h2>
        <ul>
          <li>{{ t('requests.delegations.how.decides') }}</li>
          <li>{{ t('requests.delegations.how.notified') }}</li>
          <li>{{ t('requests.delegations.how.yourself') }}</li>
          <li>{{ t('requests.delegations.how.own') }}</li>
        </ul>
      </section>
    </div>

    <DelegationFormModal v-model:show="showForm" :entry="editing" @saved="load" />
  </div>
</template>

<style scoped>
.narrow {
  max-width: 980px;
}
.section {
  margin: 0 0 10px;
}
/* The state at a glance, in the colour of what is going on. */
.banner {
  --tone: var(--ar-text-subtle);
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 16px 18px;
  border: 1px solid var(--ar-border);
  border-left: 3px solid var(--tone);
  border-radius: 3px;
  background: var(--ar-surface);
}
.banner.running {
  --tone: var(--ar-success);
}
.banner.planned {
  --tone: var(--ar-primary);
}
.banner-icon {
  display: grid;
  flex: none;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 3px;
  background: color-mix(in srgb, var(--tone) 14%, transparent);
  color: var(--tone);
}
.banner-text {
  display: grid;
  flex: 1;
  gap: 3px;
  min-width: 0;
  font-size: 13px;
}
.banner-text strong {
  font-size: 14px;
}
.departments {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  color: var(--ar-text-muted);
  font-size: 12px;
}
/* One framed list, a row per delegate. */
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
}
.line:last-child {
  border-bottom: none;
}
.line.running {
  box-shadow: inset 3px 0 0 var(--ar-success);
}
.line.ended {
  color: var(--ar-text-muted);
}
.avatar {
  display: grid;
  flex: none;
  place-items: center;
  width: 32px;
  height: 32px;
  border-radius: 3px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
  font-size: 12px;
  font-weight: 700;
}
.ended .avatar {
  background: var(--ar-surface-sunken);
  color: var(--ar-text-muted);
}
.text {
  display: grid;
  flex: 1;
  gap: 2px;
  min-width: 0;
}
.small {
  font-size: 12px;
}
.meta {
  display: flex;
  flex: none;
  align-items: center;
  gap: 14px;
}
.period {
  min-width: 170px;
  font-size: 12px;
  text-align: right;
}
.actions {
  display: flex;
  flex: none;
  gap: 2px;
}
.empty {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 28px 16px;
  border: 1px dashed var(--ar-border);
  border-radius: 3px;
  color: var(--ar-text-muted);
  text-align: center;
}
.empty p {
  margin: 0;
}
.to-approvals {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 10px;
  font-size: 13px;
}
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
.how ul {
  display: grid;
  gap: 6px;
  margin: 0;
  padding-left: 18px;
  color: var(--ar-text-muted);
  font-size: 13px;
  line-height: 1.5;
}
@media (max-width: 760px) {
  .banner {
    flex-wrap: wrap;
  }
  .line {
    flex-wrap: wrap;
    row-gap: 8px;
  }
  .line .text {
    flex-basis: calc(100% - 46px);
  }
  .meta {
    order: 3;
    width: 100%;
    justify-content: space-between;
  }
  .actions {
    order: 4;
  }
  .period {
    min-width: 0;
  }
}
</style>
