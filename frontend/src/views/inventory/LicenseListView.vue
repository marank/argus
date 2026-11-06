<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { NButton, NTag } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { usersApi } from '@/api/accounts'
import { assetsApi, licensesApi } from '@/api/inventory'
import { categoriesApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import PageHeader from '@/components/common/PageHeader.vue'
import LicenseFormDrawer from '@/components/inventory/LicenseFormDrawer.vue'
import SeatUsage from '@/components/inventory/SeatUsage.vue'
import ListTable from '@/components/table/ListTable.vue'
import TableToolbar from '@/components/table/TableToolbar.vue'
import type { TableColumn, TableFilter, TableGrouping } from '@/components/table/types'
import { toIsoDate, useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { useTableView } from '@/composables/useTableView'
import type { Id } from '@/types/common'
import { categoryIcon } from '@/utils/icons'
import { useFeaturesStore } from '@/stores/features'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
// Without the right to change licenses, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('licenses', 'write'))
const features = useFeaturesStore()
const router = useRouter()
const route = useRoute()
const { date, enumLabel, money } = useFormat()

/** "Ends soon": within the license warning period from the site settings. */
const soonDate = () => toIsoDate(Date.now() + features.rules.license_warning_days * 86_400_000)

type License = Schemas['LicenseOut']

const filters = computed<TableFilter[]>(() => [
  {
    key: 'category',
    label: t('inventory.fields.category'),
    type: 'entity',
    fetcher: categoriesApi.list,
    params: { kind: 'software' },
    display: (c: Schemas['CategoryOut']) => c.path.join(' / '),
  },
  {
    key: 'assign_to',
    label: t('inventory.licenses.assignTo'),
    type: 'select',
    options: (['user', 'device'] as const).map((v) => ({
      value: v,
      label: enumLabel('licenseAssignTo', v),
    })),
  },
  {
    key: 'user',
    label: t('inventory.fields.assignedTo'),
    type: 'entity',
    fetcher: usersApi.list,
    display: (u: Schemas['UserOut']) => u.display_name,
  },
  {
    key: 'asset',
    label: t('inventory.issues.device'),
    type: 'entity',
    fetcher: assetsApi.list,
    display: (a: Schemas['AssetOut']) => `${a.inventory_number} · ${a.model.full_name}`,
  },
  {
    key: 'valid_until',
    label: t('inventory.licenses.validUntil'),
    type: 'daterange',
    from: 'expires_from',
    until: 'expires_until',
  },
])

const groupings = (): TableGrouping<License>[] => [
  {
    key: 'category',
    label: t('inventory.fields.category'),
    ordering: 'model__category__sort_order,model__category__name',
    rowKey: (l) => l.category.id,
    rowLabel: (l) => [h(categoryIcon(l.category.icon), { size: 14 }), l.category.name],
  },
  {
    key: 'assign_to',
    label: t('inventory.licenses.assignTo'),
    ordering: 'assign_to',
    rowKey: (l) => l.assign_to,
    rowLabel: (l) => enumLabel('licenseAssignTo', l.assign_to),
  },
  {
    key: 'supplier',
    label: t('inventory.fields.supplier'),
    ordering: 'supplier__name,supplier_id',
    rowKey: (l) => l.supplier?.id ?? '',
    rowLabel: (l) =>
      l.supplier?.name ??
      h('span', { class: 'muted' }, t('table.without', { name: t('inventory.fields.supplier') })),
  },
]

const view = useTableView<License>({
  id: 'licenses',
  columns: (): TableColumn<License>[] => columns.value,
  rows: (): License[] => list.rows.value,
  groupings,
  defaultGrouping: 'category',
})

const list = useList(licensesApi.list, {
  live: ['license'],
  ordering: 'model__name',
  groupOrdering: view.groupOrdering,
  filters: {
    category: [],
    assign_to: [],
    user: [],
    asset: [],
    expires_from: null,
    // The dashboard tile links here with ?expiring=1.
    expires_until: route.query.expiring ? soonDate() : null,
  },
})
onMounted(list.load)

const showForm = ref(false)
// Most digits of the seat numbers on this page, so the seat column lines up without spare room.
const seatDigits = computed<number>(() =>
  Math.max(1, ...list.rows.value.map((l) => String(Math.max(l.seats, l.seats_used)).length)),
)

function validity(l: Schemas['LicenseOut']) {
  if (!l.valid_until) return h('span', { class: 'muted' }, t('inventory.licenses.perpetual'))
  const soon = !l.is_expired && l.valid_until < (soonDate() ?? '')
  return h('span', { class: 'validity' }, [
    h('span', { class: 'mono' }, date(l.valid_until)),
    l.is_expired
      ? h(NTag, { size: 'small', type: 'error', bordered: false }, () =>
          t('inventory.licenses.expired'),
        )
      : soon
        ? h(NTag, { size: 'small', type: 'warning', bordered: false }, () =>
            t('inventory.licenses.expiresSoon'),
          )
        : null,
  ])
}

const columns = computed<TableColumn<License>[]>(() => [
  {
    key: 'model__name',
    title: t('inventory.licenses.software'),
    sorter: true,
    hideable: false,
    minWidth: 260,
    render: (l) =>
      h('div', [
        h('div', { class: 'strong' }, l.model.full_name),
        l.reference ? h('small', { class: 'muted' }, l.reference) : null,
      ]),
  },
  {
    key: 'used_seats',
    title: t('inventory.licenses.seats'),
    sorter: true,
    width: 190,
    render: (l) => h(SeatUsage, { used: l.seats_used, seats: l.seats, digits: seatDigits.value }),
  },
  {
    key: 'assign_to',
    title: t('inventory.licenses.assignTo'),
    width: 140,
    render: (l) => enumLabel('licenseAssignTo', l.assign_to),
  },
  {
    key: 'valid_until',
    title: t('inventory.licenses.validUntil'),
    sorter: true,
    width: 200,
    render: validity,
  },
  {
    key: 'supplier',
    hidden: true,
    title: t('inventory.fields.supplier'),
    width: 170,
    ellipsis: { tooltip: true },
    render: (l) => l.supplier?.name ?? '—',
  },
  // Further columns to show from the column settings.
  {
    key: 'manufacturer',
    title: t('inventory.fields.manufacturer'),
    hidden: true,
    width: 150,
    render: (l) => l.manufacturer.name,
  },
  {
    key: 'model__category__name',
    title: t('inventory.fields.category'),
    sorter: true,
    hidden: true,
    width: 160,
    render: (l) => l.category.name,
  },
  {
    key: 'reference',
    title: t('inventory.licenses.reference'),
    sorter: true,
    hidden: true,
    width: 180,
    ellipsis: { tooltip: true },
    render: (l) => l.reference || '—',
  },
  {
    key: 'license_key',
    title: t('inventory.licenses.licenseKey'),
    hidden: true,
    width: 220,
    ellipsis: { tooltip: true },
    render: (l) => h('span', { class: 'mono' }, l.license_key || '—'),
  },
  {
    key: 'valid_from',
    title: t('inventory.licenses.validFrom'),
    hidden: true,
    width: 120,
    render: (l) => h('span', { class: 'mono' }, date(l.valid_from)),
  },
  {
    key: 'purchase_date',
    title: t('inventory.fields.purchaseDate'),
    hidden: true,
    width: 120,
    render: (l) => h('span', { class: 'mono' }, date(l.purchase_date)),
  },
  {
    key: 'purchase_price',
    title: t('inventory.fields.purchasePrice'),
    hidden: true,
    width: 120,
    align: 'right',
    render: (l) => h('span', { class: 'mono' }, money(l.purchase_price)),
  },
  {
    key: 'notes',
    title: t('common.notes'),
    hidden: true,
    width: 220,
    ellipsis: { tooltip: true },
    render: (l) => l.notes || '—',
  },
  {
    key: 'created_at',
    title: t('common.createdAt'),
    sorter: true,
    hidden: true,
    width: 120,
    render: (l) => h('span', { class: 'mono' }, date(l.created_at)),
  },
])

function open(id: Id) {
  router.push({ name: 'license', params: { id } })
}
</script>

<template>
  <div class="page">
    <PageHeader :title="t('inventory.licenses.title')" :subtitle="t('inventory.licenses.subtitle')">
      <template v-if="canWrite" #actions>
        <NButton type="primary" @click="showForm = true">
          <template #icon><Plus :size="16" /></template>
          {{ t('inventory.licenses.newLicense') }}
        </NButton>
      </template>
    </PageHeader>
    <div class="stack">
      <TableToolbar
        v-model:search="list.search.value"
        :list="list"
        :filters="filters"
        :view="view"
      />
      <ListTable :view="view" :list="list" @row-click="(l: License) => open(l.id)" />
    </div>
    <LicenseFormDrawer v-model:show="showForm" @saved="(l) => open(l.id)" />
  </div>
</template>

<style scoped>
:deep(.validity) {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
:deep(.strong) {
  font-weight: 500;
}
</style>
