<script setup lang="ts">
import type { Id } from '@/types/common'
import { CalendarClock, X } from '@lucide/vue'
import { NAlert, NButton, NCard, NDataTable, NSkeleton, type DataTableColumns } from 'naive-ui'
import { h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { reservationsApi } from '@/api/reservations'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import ReservationInfo from '@/components/reservations/ReservationInfo.vue'
import ReservationSteps from '@/components/reservations/ReservationSteps.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import type { Reservation, ReservationItem } from '@/types/reservations'
import { allocationCode, allocationModel, itemLabel } from '@/utils/reservations'

const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const route = useRoute()
const confirm = useConfirm()
const { weekday } = useFormat()
const { busy, run } = useAction()

const reservation = ref<Reservation | null>(null)

onMounted(async () => (reservation.value = await reservationsApi.get(props.id)))

async function cancel() {
  if (!(await confirm(t('reservations.actions.confirmCancel'), { danger: true }))) return
  const updated = await run(() => reservationsApi.cancel(props.id))
  if (updated) reservation.value = updated
}

const columns: DataTableColumns<ReservationItem> = [
  {
    key: 'label',
    title: () => t('reservations.items'),
    render: (i) =>
      h('div', [h('div', itemLabel(i)), i.note ? h('small', { class: 'muted' }, i.note) : null]),
  },
  {
    key: 'requested',
    title: () => t('reservations.quantities.requested'),
    width: 120,
    align: 'right',
    render: (i) => h('span', { class: 'mono' }, i.quantity_requested),
  },
  {
    key: 'approved',
    title: () => t('reservations.quantities.approved'),
    width: 120,
    align: 'right',
    render: (i) =>
      h(
        'span',
        {
          class: [
            'mono',
            i.quantity_approved !== null && i.quantity_approved < i.quantity_requested
              ? 'reduced'
              : '',
          ],
        },
        i.quantity_approved ?? '—',
      ),
  },
  {
    key: 'devices',
    title: () => t('inventory.fields.inventoryNumber'),
    render: (i) =>
      h(
        'span',
        { class: 'mono muted' },
        i.allocations.map((a) => allocationCode(a) || allocationModel(a)).join(', ') || '—',
      ),
  },
]
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!reservation" height="200px" />
    <template v-else>
      <PageHeader :title="reservation.title" :eyebrow="reservation.number">
        <template #badge
          ><StatusTag
            group="reservationStatus"
            :value="reservation.status"
            :pulse="reservation.status === 'ready'"
        /></template>
        <template #actions>
          <NButton
            v-if="['submitted', 'approved', 'ready'].includes(reservation.status)"
            :loading="busy"
            @click="cancel"
          >
            <template #icon><X :size="15" /></template>
            {{ t('reservations.actions.cancel') }}
          </NButton>
        </template>
      </PageHeader>

      <div class="stack">
        <NAlert v-if="route.query.created" type="success" :bordered="false">
          {{ t('reservations.new.submitted', { number: reservation.number }) }}
        </NAlert>
        <NAlert v-if="reservation.status === 'ready' && reservation.pickup_at" type="success">
          <template #icon><CalendarClock :size="18" /></template>
          <strong>{{ t('dashboard.pickupAt', { date: weekday(reservation.pickup_at) }) }}</strong>
          <span v-if="reservation.pickup_location">
            · {{ reservation.pickup_location.full_name }}</span
          >
        </NAlert>

        <NCard size="small"><ReservationSteps :reservation="reservation" /></NCard>
        <NCard size="small"><ReservationInfo :reservation="reservation" /></NCard>
        <NCard :title="t('reservations.items')" size="small">
          <NDataTable size="small" :columns="columns" :data="reservation.items" :bordered="false" />
        </NCard>
      </div>
    </template>
  </div>
</template>

<style scoped>
:deep(.reduced) {
  color: var(--ar-warning);
  font-weight: 600;
}
</style>
