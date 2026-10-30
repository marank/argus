<script setup lang="ts">
import { NDataTable, NInput, NSelect, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { eventsApi } from '@/api/inventory'
import { assetModelsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import DateField from '@/components/common/DateField.vue'
import { toIsoDate, useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { modelLabel } from '@/utils/models'

const { t } = useI18n()
const { dateTime, enumLabel, money } = useFormat()

const ALL_KINDS = allValues<Schemas['AssetEventKind']>({
  battery_replaced: true,
  component_replaced: true,
  repair: true,
  maintenance: true,
  inspection: true,
  note: true,
  assigned: true,
  returned: true,
  reserved: true,
  status_changed: true,
  created: true,
  issue_reported: true,
  issue_resolved: true,
})

const list = useList(eventsApi.list, {
  live: ['asset'],
  filters: {
    kind: ['battery_replaced', 'component_replaced', 'repair', 'maintenance', 'inspection'],
    model: null,
    since: null,
    until: null,
  },
})
onMounted(list.load)

const range = ref<[number, number] | null>(null)
watch(range, (value) => {
  list.filters.since = value ? toIsoDate(value[0]) : null
  list.filters.until = value ? toIsoDate(value[1]) : null
})

const kindOptions = computed(() =>
  ALL_KINDS.map((k) => ({ value: k, label: enumLabel('eventKind', k) })),
)

const columns = computed<DataTableColumns<Schemas['AssetEventWithAssetOut']>>(() => [
  {
    key: 'occurred_at',
    title: t('inventory.event.occurredAt'),
    width: 150,
    render: (e) => h('span', { class: 'mono' }, dateTime(e.occurred_at)),
  },
  {
    key: 'asset',
    title: t('inventory.event.asset'),
    width: 260,
    render: (e) =>
      h('div', [
        h(
          RouterLink,
          { to: { name: 'asset', params: { id: e.asset.id } }, class: 'mono' },
          () => e.asset.inventory_number,
        ),
        h('small', { class: 'muted', style: 'display:block' }, e.asset.model.full_name),
      ]),
  },
  {
    key: 'kind',
    title: t('inventory.event.kind'),
    width: 170,
    render: (e) => enumLabel('eventKind', e.kind),
  },
  {
    key: 'component',
    title: t('inventory.event.component'),
    width: 170,
    render: (e) => e.component || '—',
  },
  {
    key: 'description',
    title: t('common.description'),
    ellipsis: { tooltip: true },
    render: (e) => e.description || e.related_user?.display_name || '—',
  },
  {
    key: 'cost',
    title: t('inventory.event.cost'),
    width: 100,
    align: 'right',
    render: (e) => h('span', { class: 'mono' }, money(e.cost)),
  },
  {
    key: 'performed_by',
    title: t('inventory.event.performedBy'),
    width: 140,
    render: (e) => e.performed_by?.display_name ?? '—',
  },
])
</script>

<template>
  <div class="page">
    <PageHeader :title="t('inventory.eventLog')" :subtitle="t('inventory.eventLogSubtitle')" />
    <div class="stack">
      <div class="toolbar">
        <NInput
          v-model:value="list.search.value"
          class="grow"
          :placeholder="t('common.search')"
          clearable
        />
        <NSelect
          v-model:value="list.filters.kind as string[]"
          :options="kindOptions"
          multiple
          clearable
          max-tag-count="responsive"
          :placeholder="t('inventory.event.kind')"
          style="width: 300px"
        />
        <EntitySelect
          v-model="list.filters.model as string | null"
          :fetcher="assetModelsApi.list"
          :params="{ tracking: 'serialized' }"
          :label="modelLabel"
          :placeholder="t('inventory.fields.model')"
          style="width: 220px"
        />
        <DateField v-model:value="range" type="daterange" clearable style="width: 260px" />
      </div>
      <NDataTable
        remote
        size="small"
        :columns="columns"
        :data="list.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(e: Schemas['AssetEventWithAssetOut']) => e.id"
        :scroll-x="1100"
      />
    </div>
  </div>
</template>
