<script setup lang="ts">
import { NDataTable, type DataTableColumns } from 'naive-ui'
import { h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { portalApi } from '@/api/reservations'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useFormat } from '@/composables/useFormat'
import type { MyAsset } from '@/types/reservations'

const { t } = useI18n()
const { date } = useFormat()
const assets = ref<MyAsset[] | null>(null)

onMounted(async () => (assets.value = await portalApi.myAssets()))

const columns: DataTableColumns<MyAsset> = [
  {
    key: 'inventory_number',
    title: () => t('inventory.fields.inventoryNumber'),
    width: 140,
    render: (a) => h('span', { class: 'mono' }, a.inventory_number),
  },
  { key: 'model', title: () => t('inventory.fields.model'), render: (a) => a.model.full_name },
  { key: 'category', title: () => t('inventory.fields.category') },
  {
    key: 'serial',
    title: () => t('inventory.fields.serialNumber'),
    render: (a) => h('span', { class: 'mono' }, a.serial_number || '—'),
  },
  {
    key: 'since',
    title: () => t('inventory.fields.assignedSince'),
    width: 130,
    render: (a) => h('span', { class: 'mono' }, date(a.assigned_since)),
  },
  {
    key: 'due',
    title: () => t('reservations.endDate'),
    width: 200,
    render: (a) =>
      a.return_due
        ? h('span', { class: 'mono' }, `${date(a.return_due)} · ${a.reservation_number}`)
        : h('span', { class: 'muted' }, t('common.permanent')),
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
      size="small"
      :columns="columns"
      :data="assets ?? []"
      :loading="!assets"
      :scroll-x="820"
    />
  </div>
</template>
