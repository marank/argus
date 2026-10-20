<script setup lang="ts">
import { NDataTable, NRadioButton, NRadioGroup, type DataTableColumns } from 'naive-ui'
import { computed, h, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { approvalsApi } from '@/api/reservations'
import EmptyState from '@/components/common/EmptyState.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import type { ReservationListItem } from '@/types/reservations'

/** Requests of the approver's departments: waiting ones (oldest first) or those decided. */
const { t } = useI18n()
const router = useRouter()
const { date } = useFormat()

const show = ref<'pending' | 'decided'>('pending')
const requests = ref<ReservationListItem[] | null>(null)

watch(
  show,
  async (value) => {
    requests.value = null
    const page = await approvalsApi.list({ pending: value === 'pending', page_size: 100 })
    requests.value = page.items
  },
  { immediate: true },
)

const period = (r: ReservationListItem) =>
  `${date(r.start_date)} → ${r.end_date ? date(r.end_date) : t('common.permanent')}`

const columns = computed<DataTableColumns<ReservationListItem>>(() => [
  {
    key: 'number',
    title: t('reservations.number'),
    width: 120,
    render: (r) => h('span', { class: 'mono' }, r.number),
  },
  {
    key: 'requester',
    title: t('reservations.requester'),
    minWidth: 180,
    render: (r) =>
      h('div', [
        h('div', r.requester.display_name),
        r.department ? h('small', { class: 'muted' }, r.department.name) : null,
      ]),
  },
  {
    key: 'title',
    title: t('reservations.purpose'),
    minWidth: 240,
    render: (r) => h('div', [h('div', r.title), h('small', { class: 'muted' }, r.summary)]),
  },
  {
    key: 'period',
    title: t('reservations.period'),
    width: 200,
    render: (r) => h('span', { class: 'mono' }, period(r)),
  },
  {
    key: 'status',
    title: t('common.status'),
    width: 150,
    render: (r) => h(StatusTag, { group: 'reservationStatus', value: r.status }),
  },
  {
    key: 'created_at',
    title: t('common.createdAt'),
    width: 120,
    render: (r) => h('span', { class: 'mono' }, date(r.created_at)),
  },
])
</script>

<template>
  <div class="page">
    <PageHeader
      :title="t('reservations.approvals.title')"
      :subtitle="t('reservations.approvals.subtitle')"
    >
      <template #actions>
        <NRadioGroup v-model:value="show" size="small">
          <NRadioButton value="pending">{{ t('reservations.approvals.pending') }}</NRadioButton>
          <NRadioButton value="decided">{{ t('reservations.approvals.decided') }}</NRadioButton>
        </NRadioGroup>
      </template>
    </PageHeader>
    <EmptyState
      v-if="requests && !requests.length"
      :text="
        t(
          show === 'pending'
            ? 'reservations.approvals.empty'
            : 'reservations.approvals.emptyDecided',
        )
      "
    />
    <NDataTable
      v-else
      class="clickable-rows"
      size="small"
      :columns="columns"
      :data="requests ?? []"
      :loading="!requests"
      :row-key="(r: ReservationListItem) => r.id"
      :row-props="
        (r: ReservationListItem) => ({
          onClick: () => router.push({ name: 'portal-approval', params: { id: r.id } }),
        })
      "
      :scroll-x="1000"
    />
  </div>
</template>
