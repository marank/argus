<script setup lang="ts">
import { ChevronRight, MessageSquareWarning } from '@lucide/vue'
import { useMediaQuery } from '@vueuse/core'
import { NButton, NDataTable, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { portalApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ReportIssueModal from '@/components/portal/ReportIssueModal.vue'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import { isPast } from '@/utils/requests'
import { categoryIcon } from '@/utils/icons'
import { useFeaturesStore } from '@/stores/features'

/** Devices handed out to the employee; a row opens the device, the button reports a problem. */
const { t } = useI18n()
const features = useFeaturesStore()
const router = useRouter()
const { date } = useFormat()
const assets = ref<Schemas['MyAssetOut'][] | null>(null)
const reporting = ref<Schemas['MyAssetOut'] | null>(null)
const showReport = ref(false)
/** Phones get one card per device instead of a table too wide for them. */
const narrow = useMediaQuery('(max-width: 640px)')

async function load() {
  assets.value = await portalApi.myAssets()
}
onMounted(load)
useLive(['asset', 'request'], load, { paused: () => showReport.value })

function report(asset: Schemas['MyAssetOut']) {
  reporting.value = asset
  showReport.value = true
}

/** Small badge next to the device name while a report is open or in progress. */
function reportBadge(a: Schemas['MyAssetOut']) {
  const issue = a.issues.find((i) => i.status !== 'resolved')
  if (!issue) return null
  const inProgress = issue.status === 'in_progress'
  return h(
    'span',
    { class: ['report-badge', { 'in-progress': inProgress }] },
    t(inProgress ? 'requests.myDevices.reportInProgress' : 'requests.myDevices.reportOpen'),
  )
}

const columns = computed<DataTableColumns<Schemas['MyAssetOut']>>(() => [
  {
    key: 'model',
    title: () => t('requests.myDevices.device'),
    minWidth: 240,
    render: (a) =>
      h('div', { class: 'device-cell' }, [
        h(categoryIcon(a.category_icon), { size: 16, class: 'muted' }),
        h('div', [
          h('div', { class: 'device-name' }, [a.model.full_name, reportBadge(a)]),
          h('small', { class: 'muted' }, a.category),
        ]),
      ]),
  },
  {
    key: 'inventory_number',
    title: () => t('inventory.fields.inventoryNumber'),
    width: 130,
    render: (a) => h('span', { class: 'mono' }, a.inventory_number),
  },
  {
    key: 'serial',
    title: () => t('inventory.fields.serialNumber'),
    width: 150,
    render: (a) => h('span', { class: 'mono' }, a.serial_number || '—'),
  },
  {
    key: 'since',
    title: () => t('inventory.fields.assignedSince'),
    width: 120,
    render: (a) => h('span', { class: 'mono' }, date(a.assigned_since)),
  },
  {
    key: 'due',
    title: () => t('requests.myDevices.returnBy'),
    width: 130,
    render: (a) =>
      a.return_due
        ? h(
            'span',
            {
              class: ['mono', { overdue: isPast(a.return_due) }],
              title: isPast(a.return_due) ? t('requests.myDevices.overdue') : undefined,
            },
            date(a.return_due),
          )
        : h('span', { class: 'muted' }, t('common.permanent')),
  },
  // Problem reports can be switched off in the site settings.
  ...(features.isOn('issues')
    ? ([
        {
          key: 'actions',
          title: '',
          width: 160,
          align: 'right',
          render: (a) =>
            h(
              NButton,
              {
                size: 'small',
                secondary: true,
                onClick: (e: Event) => (e.stopPropagation(), report(a)),
              },
              {
                icon: () => h(MessageSquareWarning, { size: 15 }),
                default: () => t('requests.myDevices.report'),
              },
            ),
        },
      ] as DataTableColumns<Schemas['MyAssetOut']>)
    : []),
])
</script>

<template>
  <div class="page">
    <PageHeader
      :title="t('requests.myDevices.title')"
      :subtitle="t('requests.myDevices.subtitle')"
    />
    <EmptyState v-if="assets && !assets.length" :text="t('requests.myDevices.empty')" />
    <div v-else-if="narrow && assets" class="cards">
      <RouterLink
        v-for="a in assets"
        :key="a.id"
        :to="{ name: 'portal-device', params: { id: a.id } }"
        class="card"
      >
        <div class="card-head">
          <component :is="categoryIcon(a.category_icon)" :size="18" class="muted" />
          <div class="titles">
            <strong class="device-name"
              >{{ a.model.full_name }} <component :is="() => reportBadge(a)"
            /></strong>
            <small class="muted"
              >{{ a.category }} · <span class="mono">{{ a.inventory_number }}</span></small
            >
          </div>
          <ChevronRight :size="16" class="muted" />
        </div>
        <div class="card-foot">
          <span v-if="a.return_due" class="mono small" :class="{ overdue: isPast(a.return_due) }">{{
            isPast(a.return_due)
              ? t('requests.myDevices.overdueSince', { date: date(a.return_due) })
              : t('requests.myDevices.returnByDate', { date: date(a.return_due) })
          }}</span>
          <span v-else class="muted small">{{ t('requests.myDevices.permanent') }}</span>
          <NButton
            v-if="features.isOn('issues')"
            size="small"
            secondary
            @click.prevent.stop="report(a)"
          >
            <template #icon><MessageSquareWarning :size="15" /></template>
            {{ t('requests.myDevices.report') }}
          </NButton>
        </div>
      </RouterLink>
    </div>
    <NDataTable
      v-else
      class="clickable-rows"
      size="small"
      :columns="columns"
      :data="assets ?? []"
      :loading="!assets"
      :row-key="(a: Schemas['MyAssetOut']) => a.id"
      :row-props="
        (a: Schemas['MyAssetOut']) => ({
          onClick: () => router.push({ name: 'portal-device', params: { id: a.id } }),
        })
      "
      :scroll-x="1000"
    />
    <ReportIssueModal v-model:show="showReport" :asset="reporting" @reported="load" />
  </div>
</template>

<style scoped>
:deep(.device-name) {
  display: flex;
  align-items: center;
  gap: 8px;
}
:deep(.report-badge) {
  --tone: var(--ar-warning);
  padding: 0 6px;
  border: 1px solid color-mix(in srgb, var(--tone) 40%, transparent);
  border-radius: 999px;
  background: color-mix(in srgb, var(--tone) 12%, transparent);
  color: var(--tone);
  font-size: 10.5px;
  font-weight: 600;
  line-height: 16px;
  white-space: nowrap;
}
:deep(.report-badge.in-progress) {
  --tone: var(--ar-info);
}
:deep(.overdue) {
  color: var(--ar-error);
  font-weight: 600;
}
.cards {
  display: grid;
  gap: 10px;
}
.card {
  display: grid;
  gap: 10px;
  padding: 12px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  color: inherit;
  text-decoration: none;
}
.card-head {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 10px;
  align-items: center;
}
.titles {
  display: grid;
  gap: 2px;
}
.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
}
.small {
  font-size: 12px;
}
:deep(.device-cell) {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
