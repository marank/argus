<script setup lang="ts">
import { PackagePlus } from '@lucide/vue'
import { NButton, NDataTable, type DataTableColumns } from 'naive-ui'
import { h, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { reservationsApi } from '@/api/reservations'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import type { ReservationListItem } from '@/types/reservations'

const { t } = useI18n()
const router = useRouter()
const { date, weekday } = useFormat()
const list = useList((params) => reservationsApi.list({ ...params, mine: true }), {
  ordering: '-created_at',
})

onMounted(list.load)

const columns: DataTableColumns<ReservationListItem> = [
  {
    key: 'number',
    title: () => t('reservations.number'),
    width: 140,
    render: (r) => h('span', { class: 'mono' }, r.number),
  },
  { key: 'title', title: () => t('reservations.purpose'), ellipsis: { tooltip: true } },
  { key: 'summary', title: () => t('reservations.items'), ellipsis: { tooltip: true } },
  {
    key: 'period',
    title: () => t('reservations.period'),
    width: 210,
    render: (r) =>
      h(
        'span',
        { class: 'mono' },
        `${date(r.start_date)} → ${r.end_date ? date(r.end_date) : t('common.permanent')}`,
      ),
  },
  {
    key: 'pickup_at',
    title: () => t('reservations.pickupAt'),
    width: 170,
    render: (r) => h('span', { class: 'mono' }, r.pickup_at ? weekday(r.pickup_at) : '—'),
  },
  {
    key: 'status',
    title: () => t('common.status'),
    width: 150,
    render: (r) => h(StatusTag, { group: 'reservationStatus', value: r.status }),
  },
]
</script>

<template>
  <div class="page">
    <PageHeader :title="t('reservations.mine.title')" :subtitle="t('reservations.mine.subtitle')">
      <template #actions>
        <RouterLink :to="{ name: 'portal-new' }">
          <NButton type="primary">
            <template #icon><PackagePlus :size="16" /></template>
            {{ t('nav.newRequest') }}
          </NButton>
        </RouterLink>
      </template>
    </PageHeader>

    <EmptyState
      v-if="!list.loading.value && !list.count.value"
      :text="t('reservations.mine.empty')"
    />
    <NDataTable
      v-else
      class="clickable-rows"
      remote
      size="small"
      :columns="columns"
      :data="list.rows.value"
      :loading="list.loading.value"
      :pagination="list.pagination.value"
      :row-key="(r: ReservationListItem) => r.id"
      :row-props="
        (r: ReservationListItem) => ({
          onClick: () => router.push({ name: 'portal-request', params: { id: r.id } }),
        })
      "
      :scroll-x="900"
    />
  </div>
</template>
