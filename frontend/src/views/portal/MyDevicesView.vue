<script setup lang="ts">
import { MessageSquareWarning } from '@lucide/vue'
import { NButton, NDataTable, type DataTableColumns } from 'naive-ui'
import { h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { portalApi } from '@/api/reservations'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ReportIssueModal from '@/components/portal/ReportIssueModal.vue'
import { useFormat } from '@/composables/useFormat'
import type { MyAsset } from '@/types/reservations'
import { categoryIcon } from '@/utils/icons'

/** Devices handed out to the employee; a row opens the device, the button reports a problem. */
const { t } = useI18n()
const router = useRouter()
const { date } = useFormat()
const assets = ref<MyAsset[] | null>(null)
const reporting = ref<MyAsset | null>(null)
const showReport = ref(false)

async function load() {
  assets.value = await portalApi.myAssets()
}
onMounted(load)

function report(asset: MyAsset) {
  reporting.value = asset
  showReport.value = true
}

/** The open report if there is one, otherwise the most recent (recently resolved) one. */
const latestIssue = (a: MyAsset) => a.issues.find((i) => i.status !== 'resolved') ?? a.issues[0]

const columns: DataTableColumns<MyAsset> = [
  {
    key: 'model',
    title: () => t('reservations.myDevices.device'),
    minWidth: 240,
    render: (a) =>
      h('div', { class: 'device-cell' }, [
        h(categoryIcon(a.category_icon), { size: 16, class: 'muted' }),
        h('div', [h('div', a.model.full_name), h('small', { class: 'muted' }, a.category)]),
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
    title: () => t('reservations.myDevices.returnBy'),
    width: 130,
    render: (a) =>
      a.return_due
        ? h('span', { class: 'mono' }, date(a.return_due))
        : h('span', { class: 'muted' }, t('common.permanent')),
  },
  {
    key: 'issues',
    title: () => t('reservations.myDevices.reports'),
    width: 150,
    render: (a) => {
      const issue = latestIssue(a)
      return issue ? h(StatusTag, { group: 'issueStatus', value: issue.status }) : '—'
    },
  },
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
          default: () => t('reservations.myDevices.report'),
        },
      ),
  },
]
</script>

<template>
  <div class="page">
    <PageHeader
      :title="t('reservations.myDevices.title')"
      :subtitle="t('reservations.myDevices.subtitle')"
    />
    <EmptyState v-if="assets && !assets.length" :text="t('reservations.myDevices.empty')" />
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
:deep(.device-cell) {
  display: flex;
  align-items: center;
  gap: 10px;
}
</style>
