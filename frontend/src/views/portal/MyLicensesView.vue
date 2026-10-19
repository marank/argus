<script setup lang="ts">
import { NDataTable, NTag, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { portalApi } from '@/api/reservations'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { toIsoDate, useFormat } from '@/composables/useFormat'
import type { OwnLicense } from '@/types/inventory'
import { categoryIcon } from '@/utils/icons'
import { useFeaturesStore } from '@/stores/features'

/** Software the employee uses: seats assigned to them or to one of their devices. */
const { t } = useI18n()
const features = useFeaturesStore()
const { date } = useFormat()

const licenses = ref<OwnLicense[] | null>(null)
onMounted(async () => (licenses.value = await portalApi.myLicenses()))

const soon = toIsoDate(Date.now() + features.rules.license_warning_days * 86_400_000) ?? ''

function validity(l: OwnLicense) {
  if (!l.valid_until) return h('span', { class: 'muted' }, t('inventory.licenses.perpetual'))
  const tag = l.is_expired
    ? h(NTag, { size: 'small', type: 'error', bordered: false }, () =>
        t('inventory.licenses.expired'),
      )
    : l.valid_until < soon
      ? h(NTag, { size: 'small', type: 'warning', bordered: false }, () =>
          t('inventory.licenses.expiresSoon'),
        )
      : null
  return h('span', { class: 'validity' }, [h('span', { class: 'mono' }, date(l.valid_until)), tag])
}

const columns = computed<DataTableColumns<OwnLicense>>(() => [
  {
    key: 'software',
    title: t('reservations.mySoftware.software'),
    minWidth: 240,
    render: (l) =>
      h('div', { class: 'software-cell' }, [
        h(categoryIcon(l.category_icon), { size: 16, class: 'muted' }),
        h('span', l.model.full_name),
      ]),
  },
  {
    key: 'via',
    title: t('reservations.mySoftware.usedVia'),
    minWidth: 220,
    render: (l) =>
      l.device
        ? h(RouterLink, { to: { name: 'portal-device', params: { id: l.device.id } } }, () => [
            h('span', { class: 'mono' }, l.device!.inventory_number),
            ` · ${l.device!.model.full_name}`,
          ])
        : t('reservations.mySoftware.personal'),
  },
  {
    key: 'valid_until',
    title: t('inventory.licenses.validUntil'),
    width: 220,
    render: validity,
  },
  {
    key: 'since',
    title: t('reservations.mySoftware.since'),
    width: 120,
    render: (l) => h('span', { class: 'mono' }, date(l.assigned_at)),
  },
])
</script>

<template>
  <div class="page">
    <PageHeader
      :title="t('reservations.mySoftware.title')"
      :subtitle="t('reservations.mySoftware.subtitle')"
    />
    <EmptyState v-if="licenses && !licenses.length" :text="t('reservations.mySoftware.empty')" />
    <NDataTable
      v-else
      size="small"
      :columns="columns"
      :data="licenses ?? []"
      :loading="!licenses"
      :row-key="(l: OwnLicense) => l.id"
      :scroll-x="820"
    />
  </div>
</template>

<style scoped>
:deep(.software-cell) {
  display: flex;
  align-items: center;
  gap: 10px;
}
:deep(.validity) {
  display: inline-flex;
  align-items: center;
  gap: 8px;
}
</style>
