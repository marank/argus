<script setup lang="ts">
import type { Id } from '@/types/common'
import { modelLabel } from '@/utils/models'
import { Layers, Plus, ScanBarcode } from '@lucide/vue'
import { NButton, NDataTable, NInput, NSelect, type DataTableColumns } from 'naive-ui'
import { useStorage } from '@vueuse/core'
import { computed, h, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { usersApi } from '@/api/accounts'
import { assetsApi } from '@/api/inventory'
import { assetModelsApi, categoriesApi, locationsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import CheckField from '@/components/common/CheckField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import AssetFormDrawer from '@/components/inventory/AssetFormDrawer.vue'
import BulkCreateModal from '@/components/inventory/BulkCreateModal.vue'
import SeriesCreateModal from '@/components/inventory/SeriesCreateModal.vue'
import { useFormat } from '@/composables/useFormat'
import { useGroupedRows, withGroupHeaders } from '@/composables/useGroupedRows'
import { useList } from '@/composables/useList'
import { ASSET_STATUSES } from '@/types/inventory'
import { categoryIcon } from '@/utils/icons'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
// Without the right to change assets, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('assets', 'write'))
const route = useRoute()
const router = useRouter()
const { date, enumLabel } = useFormat()

const queryId = (key: string) => (route.query[key] ? String(route.query[key]) : null)

/** Sections per category; the server sorts by category first. */
const grouped = useStorage('argus.assets-grouped', true)

const list = useList(assetsApi.list, {
  live: ['asset'],
  ordering: 'inventory_number',
  groupOrdering: () =>
    grouped.value ? 'model__category__sort_order,model__category__name' : undefined,
  filters: {
    status: route.query.status ? [String(route.query.status)] : [],
    category: queryId('category'),
    model: queryId('model'),
    location: null,
    assigned_to: null,
    is_loanable: null,
    warranty_until: route.query.warranty_until ? String(route.query.warranty_until) : null,
  },
})
onMounted(list.load)
watch(grouped, list.reload)

const showForm = ref(false)
const showBulk = ref(false)
const showSeries = ref(false)
const statusOptions = computed(() =>
  ASSET_STATUSES.map((s) => ({ value: s, label: enumLabel('assetStatus', s) })),
)
const loanableOnly = computed({
  get: () => list.filters.is_loanable === true,
  set: (value: boolean) => (list.filters.is_loanable = value ? true : null),
})

const baseColumns = computed<DataTableColumns<Schemas['AssetOut']>>(() => [
  {
    key: 'inventory_number',
    title: t('inventory.fields.inventoryNumber'),
    sorter: true,
    width: 130,
    fixed: 'left',
    render: (a) => h('span', { class: 'mono strong' }, a.inventory_number),
  },
  {
    key: 'model__name',
    title: t('inventory.fields.model'),
    sorter: true,
    minWidth: 220,
    render: (a) =>
      h('div', { class: 'model-cell' }, [
        h(categoryIcon(a.category.icon), { size: 15, class: 'muted' }),
        h('div', [h('div', a.model.full_name), h('small', { class: 'muted' }, a.category.name)]),
      ]),
  },
  {
    key: 'serial_number',
    title: t('inventory.fields.serialNumber'),
    sorter: true,
    width: 150,
    render: (a) => h('span', { class: 'mono' }, a.serial_number || '—'),
  },
  {
    key: 'identifier',
    title: t('inventory.fields.identifier'),
    sorter: true,
    width: 170,
    render: (a) =>
      a.identifier
        ? h(
            'span',
            { class: 'mono', title: a.category.identifier_label || undefined },
            a.identifier,
          )
        : '—',
  },
  {
    key: 'status',
    title: t('common.status'),
    sorter: true,
    width: 140,
    render: (a) => h(StatusTag, { group: 'assetStatus', value: a.status }),
  },
  {
    key: 'assigned_to__last_name',
    title: t('inventory.fields.assignedTo'),
    sorter: true,
    width: 170,
    render: (a) =>
      a.assigned_to?.display_name ??
      // Set aside, not yet handed out: for whom and with which request.
      (a.reserved_for
        ? h('span', { class: 'muted' }, [
            t('inventory.reservedFor', { name: a.reserved_for.requester.display_name }),
            h('small', { class: 'mono reserved-number' }, a.reserved_for.number),
          ])
        : '—'),
  },
  {
    key: 'location__name',
    title: t('inventory.fields.location'),
    sorter: true,
    width: 190,
    ellipsis: { tooltip: true },
    render: (a) => a.location?.full_name ?? '—',
  },
  {
    key: 'warranty_until',
    title: t('inventory.fields.warrantyUntil'),
    sorter: true,
    width: 120,
    render: (a) => h('span', { class: 'mono' }, date(a.warranty_until)),
  },
])

const columns = computed(() =>
  grouped.value ? withGroupHeaders(baseColumns.value) : baseColumns.value,
)
const grouping = useGroupedRows<Schemas['AssetOut']>({
  rows: () => list.rows.value,
  key: (a) => a.category.id,
  label: (a) => [h(categoryIcon(a.category.icon), { size: 14 }), a.category.name],
  enabled: () => grouped.value,
  storageKey: 'argus.groups.assets',
})
const openAsset = (a: Schemas['AssetOut']) => router.push({ name: 'asset', params: { id: a.id } })

function onSaved(asset: { id: Id }) {
  router.push({ name: 'asset', params: { id: asset.id } })
}
</script>

<template>
  <div class="page">
    <PageHeader :title="t('inventory.assets')" :subtitle="t('inventory.assetsSubtitle')">
      <template v-if="canWrite" #actions>
        <NButton @click="showBulk = true">
          <template #icon><ScanBarcode :size="16" /></template>
          {{ t('inventory.bulkCreate') }}
        </NButton>
        <NButton @click="showSeries = true">
          <template #icon><Layers :size="16" /></template>
          {{ t('inventory.seriesCreate') }}
        </NButton>
        <NButton type="primary" @click="showForm = true">
          <template #icon><Plus :size="16" /></template>
          {{ t('inventory.newAsset') }}
        </NButton>
      </template>
    </PageHeader>

    <div class="stack">
      <div class="toolbar">
        <NInput
          v-model:value="list.search.value"
          class="grow"
          :placeholder="t('common.search')"
          clearable
        />
        <NSelect
          v-model:value="list.filters.status as string[]"
          :options="statusOptions"
          multiple
          clearable
          :placeholder="t('common.status')"
          style="width: 220px"
          max-tag-count="responsive"
        />
        <EntitySelect
          v-model="list.filters.category as string | null"
          :fetcher="categoriesApi.list"
          :params="{ kind: 'hardware' }"
          :label="(c) => c.path.join(' / ')"
          :placeholder="t('inventory.fields.category')"
          style="width: 200px"
        />
        <EntitySelect
          v-model="list.filters.model as string | null"
          :fetcher="assetModelsApi.list"
          :params="{ tracking: 'serialized' }"
          :label="modelLabel"
          :placeholder="t('inventory.fields.model')"
          style="width: 220px"
        />
        <EntitySelect
          v-model="list.filters.location as string | null"
          :fetcher="locationsApi.list"
          :label="(l) => l.full_name"
          :placeholder="t('inventory.fields.location')"
          style="width: 190px"
        />
        <EntitySelect
          v-model="list.filters.assigned_to as string | null"
          :fetcher="usersApi.list"
          :label="(u) => u.display_name"
          :placeholder="t('inventory.fields.assignedTo')"
          style="width: 180px"
        />
        <CheckField v-model="loanableOnly" :label="t('inventory.fields.loanable')" />
        <CheckField v-model="grouped" :label="t('inventory.groupByCategory')" />
      </div>

      <NDataTable
        class="clickable-rows"
        remote
        size="small"
        :columns="columns"
        :data="grouping.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(a: Schemas['AssetOut']) => a.id"
        :row-props="(a: Schemas['AssetOut']) => grouping.rowProps(a, openAsset)"
        :row-class-name="grouping.rowClass"
        :scroll-x="1270"
        @update:sorter="list.onSort"
      />
    </div>

    <AssetFormDrawer v-model:show="showForm" @saved="onSaved" />
    <BulkCreateModal v-model:show="showBulk" @created="list.reload" />
    <SeriesCreateModal v-model:show="showSeries" @created="list.reload" />
  </div>
</template>

<style scoped>
:deep(.model-cell) {
  display: flex;
  align-items: center;
  gap: 10px;
}
:deep(.strong) {
  font-weight: 600;
}
:deep(.reserved-number) {
  display: block;
  font-size: 11px;
}
</style>
