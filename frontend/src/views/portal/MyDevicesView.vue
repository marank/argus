<script setup lang="ts">
import { MessageSquareWarning } from '@lucide/vue'
import { NButton, NDataTable, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { portalApi } from '@/api/requests'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ReportIssueModal from '@/components/portal/ReportIssueModal.vue'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import type { MyAsset } from '@/types/requests'
import { categoryIcon } from '@/utils/icons'
import { useFeaturesStore } from '@/stores/features'

/** Devices handed out to the employee; a row opens the device, the button reports a problem. */
const { t } = useI18n()
const features = useFeaturesStore()
const router = useRouter()
const { date } = useFormat()
const assets = ref<MyAsset[] | null>(null)
const reporting = ref<MyAsset | null>(null)
const showReport = ref(false)

async function load() {
  assets.value = await portalApi.myAssets()
}
onMounted(load)
useLive(['asset', 'request'], load, { paused: () => showReport.value })

function report(asset: MyAsset) {
  reporting.value = asset
  showReport.value = true
}

/** Small badge next to the device name while a report is open or in progress. */
function reportBadge(a: MyAsset) {
  const issue = a.issues.find((i) => i.status !== 'resolved')
  if (!issue) return null
  const inProgress = issue.status === 'in_progress'
  return h(
    'span',
    { class: ['report-badge', { 'in-progress': inProgress }] },
    t(inProgress ? 'requests.myDevices.reportInProgress' : 'requests.myDevices.reportOpen'),
  )
}

const columns = computed<DataTableColumns<MyAsset>>(() => [
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
        ? h('span', { class: 'mono' }, date(a.return_due))
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
      ] as DataTableColumns<MyAsset>)
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
    <NDataTable
      v-else
      class="clickable-rows"
      size="small"
      :columns="columns"
      :data="assets ?? []"
      :loading="!assets"
      :row-key="(a: MyAsset) => a.id"
      :row-props="
        (a: MyAsset) => ({
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
:deep(.device-cell) {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
