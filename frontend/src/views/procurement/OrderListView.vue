<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { NButton, NDataTable, NInput, NSelect, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { suppliersApi } from '@/api/masterdata'
import { ordersApi } from '@/api/procurement'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { ORDER_STATUSES, type OrderListItem } from '@/types/procurement'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
// Without the right to change procurement, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('procurement', 'write'))
const route = useRoute()
const router = useRouter()
const { date, money, enumLabel } = useFormat()
const { busy, run } = useAction()

const list = useList(ordersApi.list, {
  ordering: '-created_at',
  filters: {
    status: route.query.status
      ? route.query.status === 'ordered'
        ? ['ordered', 'partially_received']
        : [String(route.query.status)]
      : [],
    supplier: null,
  },
})
onMounted(list.load)

const statusOptions = computed(() =>
  ORDER_STATUSES.map((s) => ({ value: s, label: enumLabel('orderStatus', s) })),
)

const columns = computed<DataTableColumns<OrderListItem>>(() => [
  {
    key: 'number',
    title: t('procurement.orders.number'),
    sorter: true,
    width: 140,
    render: (o) => h('span', { class: 'mono strong' }, o.number),
  },
  {
    key: 'supplier',
    title: t('procurement.orders.supplier'),
    minWidth: 180,
    render: (o) => o.supplier?.name ?? '—',
  },
  {
    key: 'supplier_reference',
    title: t('procurement.orders.supplierReference'),
    width: 160,
    render: (o) => h('span', { class: 'mono' }, o.supplier_reference || '—'),
  },
  {
    key: 'line_count',
    title: t('procurement.orders.lines'),
    width: 90,
    align: 'right',
    render: (o) => h('span', { class: 'mono' }, o.line_count),
  },
  {
    key: 'total',
    title: t('common.total'),
    width: 120,
    align: 'right',
    render: (o) => h('span', { class: 'mono' }, money(o.total)),
  },
  {
    key: 'order_date',
    title: t('procurement.orders.orderDate'),
    sorter: true,
    width: 120,
    render: (o) => h('span', { class: 'mono' }, date(o.order_date)),
  },
  {
    key: 'expected_date',
    title: t('procurement.orders.expectedDate'),
    sorter: true,
    width: 120,
    render: (o) => h('span', { class: 'mono' }, date(o.expected_date)),
  },
  {
    key: 'status',
    title: t('common.status'),
    sorter: true,
    width: 160,
    render: (o) => h(StatusTag, { group: 'orderStatus', value: o.status }),
  },
])

async function createEmpty() {
  const order = await run(() =>
    ordersApi.create({
      supplier: null,
      expected_date: null,
      supplier_reference: '',
      delivery_location: null,
      notes: '',
      lines: [{ asset_model: null, description: '—', quantity: 1, unit_price: null }],
    }),
  )
  if (order) router.push({ name: 'order', params: { id: order.id } })
}
</script>

<template>
  <div class="page">
    <PageHeader :title="t('procurement.orders.title')" :subtitle="t('procurement.orders.subtitle')">
      <template v-if="canWrite" #actions>
        <NButton type="primary" :loading="busy" @click="createEmpty">
          <template #icon><Plus :size="16" /></template>
          {{ t('procurement.orders.new') }}
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
          max-tag-count="responsive"
          :placeholder="t('common.status')"
          style="width: 240px"
        />
        <EntitySelect
          v-model="list.filters.supplier as string | null"
          :fetcher="suppliersApi.list"
          :label="(s) => s.name"
          :placeholder="t('procurement.orders.supplier')"
          style="width: 200px"
        />
      </div>
      <NDataTable
        class="clickable-rows"
        remote
        size="small"
        :columns="columns"
        :data="list.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(o: OrderListItem) => o.id"
        :row-props="
          (o: OrderListItem) => ({
            onClick: () => router.push({ name: 'order', params: { id: o.id } }),
          })
        "
        :scroll-x="1000"
        @update:sorter="list.onSort"
      />
    </div>
  </div>
</template>

<style scoped>
:deep(.strong) {
  font-weight: 600;
}
</style>
