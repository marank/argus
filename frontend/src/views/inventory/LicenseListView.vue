<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { NButton, NDataTable, NInput, NSelect, NTag, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute, useRouter } from 'vue-router'

import { licensesApi } from '@/api/inventory'
import { categoriesApi } from '@/api/masterdata'
import CheckField from '@/components/common/CheckField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import LicenseFormDrawer from '@/components/inventory/LicenseFormDrawer.vue'
import SeatUsage from '@/components/inventory/SeatUsage.vue'
import { toIsoDate, useFormat } from '@/composables/useFormat'
import { useGroupedRows, withGroupHeaders } from '@/composables/useGroupedRows'
import { useList } from '@/composables/useList'
import type { Id } from '@/types/common'
import type { License } from '@/types/inventory'
import { categoryIcon } from '@/utils/icons'
import { useFeaturesStore } from '@/stores/features'
import { useAuthStore } from '@/stores/auth'

const { t } = useI18n()
// Without the right to change licenses, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('licenses', 'write'))
const features = useFeaturesStore()
const router = useRouter()
const route = useRoute()
const { date, enumLabel } = useFormat()

/** "Ends soon": within the license warning period from the site settings. */
const soonDate = () => toIsoDate(Date.now() + features.rules.license_warning_days * 86_400_000)

const list = useList(licensesApi.list, {
  live: ['license'],
  ordering: 'model__name',
  groupOrdering: () => 'model__category__sort_order,model__category__name',
  filters: {
    category: null,
    assign_to: null,
    // The dashboard tile links here with ?expiring=1.
    expires_before: route.query.expiring ? soonDate() : null,
  },
})
onMounted(list.load)

const showForm = ref(false)
// Most digits of the seat numbers on this page, so the seat column lines up without spare room.
const seatDigits = computed(() =>
  Math.max(1, ...list.rows.value.map((l) => String(Math.max(l.seats, l.seats_used)).length)),
)
const expiringOnly = computed({
  get: () => !!list.filters.expires_before,
  set: (value: boolean) => (list.filters.expires_before = value ? soonDate() : null),
})
const assignToOptions = computed(() =>
  (['user', 'device'] as const).map((v) => ({ value: v, label: enumLabel('licenseAssignTo', v) })),
)

function validity(l: License) {
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

const columns = computed(() =>
  withGroupHeaders<License>([
    {
      key: 'model__name',
      title: t('inventory.licenses.software'),
      sorter: true,
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
      title: t('inventory.fields.supplier'),
      width: 170,
      ellipsis: { tooltip: true },
      render: (l) => l.supplier?.name ?? '—',
    },
  ] as DataTableColumns<License>),
)

const grouping = useGroupedRows<License>({
  rows: () => list.rows.value,
  key: (l) => l.category.id,
  label: (l) => [h(categoryIcon(l.category.icon), { size: 14 }), l.category.name],
  storageKey: 'argus.groups.licenses',
})

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
          :params="{ kind: 'software' }"
          :label="(c) => c.path.join(' / ')"
          :placeholder="t('inventory.fields.category')"
          style="width: 220px"
        />
        <NSelect
          v-model:value="list.filters.assign_to as string | null"
          :options="assignToOptions"
          :placeholder="t('inventory.licenses.assignTo')"
          clearable
          style="width: 170px"
        />
        <CheckField v-model="expiringOnly" :label="t('inventory.licenses.onlyExpiring')" />
      </div>
      <NDataTable
        class="clickable-rows"
        remote
        size="small"
        :columns="columns"
        :data="grouping.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(row: License) => row.id"
        :row-props="(row: License) => grouping.rowProps(row, (l) => open(l.id))"
        :row-class-name="grouping.rowClass"
        :scroll-x="960"
        @update:sorter="list.onSort"
      />
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
