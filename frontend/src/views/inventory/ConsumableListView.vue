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

import { consumablesApi } from '@/api/inventory'
import { categoriesApi, locationsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import CheckField from '@/components/common/CheckField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import RowMenu from '@/components/common/RowMenu.vue'
import ConsumableModal from '@/components/inventory/ConsumableModal.vue'
import ConsumableMoveModal from '@/components/inventory/ConsumableMoveModal.vue'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
// Without the right to change consumables, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('consumables', 'write'))
const route = useRoute()
const { dateTime, enumLabel } = useFormat()

const list = useList(consumablesApi.list, {
  live: ['consumable'],
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

const selected = ref<Schemas['ConsumableOut'] | null>(null)
const moveDirection = ref<'in' | 'out' | 'adjust'>('in')
const showMove = ref(false)
const showItem = ref(false)
const showMovements = ref(false)
const movements = ref<Schemas['ConsumableMovementOut'][]>([])

function openMove(item: Schemas['ConsumableOut'], direction: 'in' | 'out' | 'adjust') {
  selected.value = item
  moveDirection.value = direction
  showMove.value = true
}

function openItem(item: Schemas['ConsumableOut'] | null) {
  selected.value = item
  showItem.value = true
}

async function openMovements(item: Schemas['ConsumableOut']) {
  selected.value = item
  movements.value = await consumablesApi.movements(item.id)
  showMovements.value = true
}

function onRowAction(item: Schemas['ConsumableOut'], key: string) {
  if (key === 'in' || key === 'out' || key === 'adjust') openMove(item, key)
  else if (key === 'movements') openMovements(item)
  else if (key === 'edit') openItem(item)
}

const columns = computed<DataTableColumns<Schemas['ConsumableOut']>>(() => [
  {
    key: 'model__name',
    title: t('inventory.consumables.item'),
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
    title: t('inventory.consumables.onHand'),
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
    title: t('inventory.consumables.reserved'),
    width: 100,
    align: 'right',
    render: (s) => h('span', { class: 'mono muted' }, s.reserved_quantity),
  },
  {
    key: 'available',
    title: t('inventory.consumables.available'),
    width: 100,
    align: 'right',
    render: (s) => h('span', { class: 'mono' }, s.available_quantity),
  },
  {
    key: 'min',
    title: t('inventory.consumables.minimum'),
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
        // Without the right to change stock only the movements can be looked at.
        items: canWrite.value
          ? [
              { key: 'in', label: t('inventory.consumables.bookIn'), icon: ArrowDownToLine },
              { key: 'out', label: t('inventory.consumables.bookOut'), icon: ArrowUpFromLine },
              { key: 'adjust', label: t('inventory.consumables.adjust'), icon: Scale },
              {
                key: 'movements',
                label: t('inventory.consumables.movements'),
                icon: History,
                divided: true,
              },
              { key: 'edit', label: t('common.edit'), icon: Settings2 },
            ]
          : [{ key: 'movements', label: t('inventory.consumables.movements'), icon: History }],
        onSelect: (key: string) => onRowAction(s, key),
      }),
  },
])

const movementColumns = computed<DataTableColumns<Schemas['ConsumableMovementOut']>>(() => [
  {
    key: 'created_at',
    title: t('inventory.event.occurredAt'),
    width: 140,
    render: (m) => h('span', { class: 'mono' }, dateTime(m.created_at)),
  },
  {
    key: 'delta',
    title: t('inventory.consumables.delta'),
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
    title: t('inventory.consumables.reason'),
    render: (m) => enumLabel('consumableReason', m.reason),
  },
  {
    key: 'who',
    title: t('inventory.consumables.recipient'),
    render: (m) => m.recipient?.display_name ?? m.note ?? '—',
  },
])
</script>

<template>
  <div class="page">
    <PageHeader
      :title="t('inventory.consumables.title')"
      :subtitle="t('inventory.consumables.subtitle')"
    >
      <template v-if="canWrite" #actions>
        <NButton type="primary" @click="openItem(null)">
          <template #icon><Plus :size="16" /></template>
          {{ t('inventory.consumables.newItem') }}
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
        <CheckField v-model="belowOnly" :label="t('inventory.consumables.onlyBelowMinimum')" />
      </div>
      <NDataTable
        remote
        size="small"
        :columns="columns"
        :data="list.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(s: Schemas['ConsumableOut']) => s.id"
        :scroll-x="1100"
        @update:sorter="list.onSort"
      />
    </div>

    <ConsumableMoveModal
      v-model:show="showMove"
      :item="selected"
      :direction="moveDirection"
      @saved="list.load"
    />
    <ConsumableModal v-model:show="showItem" :item="selected" @saved="list.load" />
    <NDrawer v-model:show="showMovements" :width="560">
      <NDrawerContent
        :title="`${t('inventory.consumables.movements')} · ${selected?.model.full_name}`"
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
