<script setup lang="ts">
import { ArrowDownToLine, ArrowUpFromLine, History, Plus, Scale, Settings2 } from '@lucide/vue'
import {
  NButton,
  NDataTable,
  NDrawer,
  NDrawerContent,
  NInput,
  NProgress,
  type DataTableColumns,
} from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { stockApi } from '@/api/inventory'
import { categoriesApi, locationsApi } from '@/api/masterdata'
import CheckField from '@/components/common/CheckField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import RowMenu from '@/components/common/RowMenu.vue'
import StockItemModal from '@/components/inventory/StockItemModal.vue'
import StockMoveModal from '@/components/inventory/StockMoveModal.vue'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import type { StockItem, StockMovement } from '@/types/inventory'

const { t } = useI18n()
const route = useRoute()
const { dateTime, enumLabel } = useFormat()

const list = useList(stockApi.list, {
  ordering: 'model__name',
  filters: {
    below_minimum: route.query.below_minimum ? true : null,
    category: null,
    location: null,
  },
})
onMounted(list.load)

const belowOnly = computed({
  get: () => list.filters.below_minimum === true,
  set: (value: boolean) => (list.filters.below_minimum = value ? true : null),
})

const selected = ref<StockItem | null>(null)
const moveDirection = ref<'in' | 'out' | 'adjust'>('in')
const showMove = ref(false)
const showItem = ref(false)
const showMovements = ref(false)
const movements = ref<StockMovement[]>([])

function openMove(item: StockItem, direction: 'in' | 'out' | 'adjust') {
  selected.value = item
  moveDirection.value = direction
  showMove.value = true
}

function openItem(item: StockItem | null) {
  selected.value = item
  showItem.value = true
}

async function openMovements(item: StockItem) {
  selected.value = item
  movements.value = await stockApi.movements(item.id)
  showMovements.value = true
}

function onRowAction(item: StockItem, key: string) {
  if (key === 'in' || key === 'out' || key === 'adjust') openMove(item, key)
  else if (key === 'movements') openMovements(item)
  else if (key === 'edit') openItem(item)
}

const columns = computed<DataTableColumns<StockItem>>(() => [
  {
    key: 'model__name',
    title: t('inventory.stock.item'),
    sorter: true,
    minWidth: 240,
    render: (s) =>
      h('div', [h('div', s.model.full_name), h('small', { class: 'muted' }, s.category.name)]),
  },
  {
    key: 'location__name',
    title: t('inventory.fields.location'),
    sorter: true,
    width: 200,
    render: (s) => s.location.full_name,
  },
  {
    key: 'quantity',
    title: t('inventory.stock.onHand'),
    sorter: true,
    width: 190,
    render: (s) =>
      h('div', { class: 'level' }, [
        h('span', { class: ['mono', 'qty', s.is_below_minimum ? 'low' : ''] }, s.quantity),
        h(NProgress, {
          type: 'line',
          percentage: Math.min(
            100,
            s.min_quantity ? (s.quantity / (s.min_quantity * 2)) * 100 : 100,
          ),
          status: s.is_below_minimum ? 'warning' : 'success',
          showIndicator: false,
          height: 4,
          style: 'width: 90px',
        }),
      ]),
  },
  {
    key: 'reserved',
    title: t('inventory.stock.reserved'),
    width: 100,
    align: 'right',
    render: (s) => h('span', { class: 'mono muted' }, s.reserved_quantity),
  },
  {
    key: 'available',
    title: t('inventory.stock.available'),
    width: 100,
    align: 'right',
    render: (s) => h('span', { class: 'mono' }, s.available_quantity),
  },
  {
    key: 'min',
    title: t('inventory.stock.minimum'),
    width: 100,
    align: 'right',
    render: (s) => h('span', { class: 'mono muted' }, s.min_quantity),
  },
  {
    key: 'actions',
    title: '',
    width: 48,
    align: 'right',
    render: (s) =>
      h(RowMenu, {
        title: t('common.actions'),
        items: [
          { key: 'in', label: t('inventory.stock.bookIn'), icon: ArrowDownToLine },
          { key: 'out', label: t('inventory.stock.bookOut'), icon: ArrowUpFromLine },
          { key: 'adjust', label: t('inventory.stock.adjust'), icon: Scale },
          { key: 'movements', label: t('inventory.stock.movements'), icon: History, divided: true },
          { key: 'edit', label: t('common.edit'), icon: Settings2 },
        ],
        onSelect: (key: string) => onRowAction(s, key),
      }),
  },
])

const movementColumns = computed<DataTableColumns<StockMovement>>(() => [
  {
    key: 'created_at',
    title: t('inventory.event.occurredAt'),
    width: 140,
    render: (m) => h('span', { class: 'mono' }, dateTime(m.created_at)),
  },
  {
    key: 'delta',
    title: t('inventory.stock.delta'),
    width: 80,
    align: 'right',
    render: (m) =>
      h(
        'span',
        { class: ['mono', m.delta > 0 ? 'pos' : 'neg'] },
        m.delta > 0 ? `+${m.delta}` : m.delta,
      ),
  },
  {
    key: 'reason',
    title: t('inventory.stock.reason'),
    render: (m) => enumLabel('stockReason', m.reason),
  },
  {
    key: 'who',
    title: t('inventory.stock.recipient'),
    render: (m) => m.recipient?.display_name ?? m.note ?? '—',
  },
])
</script>

<template>
  <div class="page">
    <PageHeader :title="t('inventory.stock.title')" :subtitle="t('inventory.stock.subtitle')">
      <template #actions>
        <NButton type="primary" @click="openItem(null)">
          <template #icon><Plus :size="16" /></template>
          {{ t('inventory.stock.newItem') }}
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
        <EntitySelect
          v-model="list.filters.category as string | null"
          :fetcher="categoriesApi.list"
          :label="(c) => c.name"
          :placeholder="t('inventory.fields.category')"
          style="width: 200px"
        />
        <EntitySelect
          v-model="list.filters.location as string | null"
          :fetcher="locationsApi.list"
          :label="(l) => l.full_name"
          :placeholder="t('inventory.fields.location')"
          style="width: 200px"
        />
        <CheckField v-model="belowOnly" :label="t('inventory.stock.onlyBelowMinimum')" />
      </div>
      <NDataTable
        remote
        size="small"
        :columns="columns"
        :data="list.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(s: StockItem) => s.id"
        :scroll-x="1100"
        @update:sorter="list.onSort"
      />
    </div>

    <StockMoveModal
      v-model:show="showMove"
      :item="selected"
      :direction="moveDirection"
      @saved="list.load"
    />
    <StockItemModal v-model:show="showItem" :item="selected" @saved="list.load" />
    <NDrawer v-model:show="showMovements" :width="560">
      <NDrawerContent
        :title="`${t('inventory.stock.movements')} · ${selected?.model.full_name}`"
        closable
      >
        <NDataTable size="small" :columns="movementColumns" :data="movements" />
      </NDrawerContent>
    </NDrawer>
  </div>
</template>

<style scoped>
:deep(.level) {
  display: flex;
  align-items: center;
  gap: 10px;
}
:deep(.qty) {
  min-width: 32px;
  text-align: right;
  font-weight: 600;
}
:deep(.low) {
  color: var(--ar-warning);
}
:deep(.pos) {
  color: var(--ar-success);
}
:deep(.neg) {
  color: var(--ar-error);
}
</style>
