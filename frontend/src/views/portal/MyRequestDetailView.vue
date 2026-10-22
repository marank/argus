<script setup lang="ts">
import { useLive } from '@/composables/useLive'
import type { Id } from '@/types/common'
import { RotateCcw, X } from '@lucide/vue'
import { NAlert, NButton, NCard, NDataTable, NSkeleton, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRoute } from 'vue-router'

import { reservationsApi } from '@/api/reservations'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import HandoverCard from '@/components/reservations/HandoverCard.vue'
import ReservationSteps from '@/components/reservations/ReservationSteps.vue'
import OriginTag from '@/components/reservations/OriginTag.vue'
import ReturnsCard from '@/components/reservations/ReturnsCard.vue'
import ApprovalCard from '@/components/reservations/detail/ApprovalCard.vue'
import HandoverPlanCard from '@/components/reservations/detail/HandoverPlanCard.vue'
import RequestInfoCard from '@/components/reservations/detail/RequestInfoCard.vue'
import ReservationHistory from '@/components/reservations/detail/ReservationHistory.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import type { Reservation, ReservationItem } from '@/types/reservations'
import { allocationCode, allocationModel, handoverPlanned, itemLabel } from '@/utils/reservations'

const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const route = useRoute()
const confirm = useConfirm()
const { busy, run } = useAction()

const reservation = ref<Reservation | null>(null)

const load = async () => (reservation.value = await reservationsApi.get(props.id))
onMounted(load)
useLive(['reservation'], load, { id: () => props.id })

/** Lent for a period: when it is due back, then what came back. */
const showReturns = computed(() => {
  const r = reservation.value
  if (!r) return false
  return (
    r.returns.length > 0 ||
    (r.duration === 'temporary' && ['handed_out', 'completed'].includes(r.status) && !!r.handover)
  )
})

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
    key: 'confirmed',
    title: () => t('reservations.quantities.confirmed'),
    width: 120,
    align: 'right',
    render: (i) =>
      h(
        'span',
        {
          class: [
            'mono',
            i.quantity_confirmed !== null && i.quantity_confirmed < i.quantity_requested
              ? 'reduced'
              : '',
          ],
        },
        i.quantity_confirmed ?? '—',
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
            :pulse="reservation.status === 'ready'" /><OriginTag :origin="reservation.origin"
        /></template>
        <template #actions>
          <NButton
            v-if="
              ['pending_approval', 'submitted', 'confirmed', 'ready'].includes(reservation.status)
            "
            :loading="busy"
            @click="cancel"
          >
            <template #icon><X :size="15" /></template>
            {{ t('reservations.actions.cancel') }}
          </NButton>
          <RouterLink
            v-if="['rejected', 'cancelled', 'completed'].includes(reservation.status)"
            :to="{ name: 'portal-new', query: { from: reservation.id } }"
          >
            <NButton :type="reservation.status === 'completed' ? 'default' : 'primary'">
              <template #icon><RotateCcw :size="15" /></template>
              {{ t('reservations.again.action') }}
            </NButton>
          </RouterLink>
        </template>
      </PageHeader>

      <div class="stack">
        <NAlert v-if="route.query.created" type="success" :bordered="false">
          {{
            t(
              reservation.status === 'pending_approval'
                ? 'reservations.new.submittedForApproval'
                : 'reservations.new.submitted',
              { number: reservation.number },
            )
          }}
        </NAlert>
        <NCard size="small"><ReservationSteps :reservation="reservation" /></NCard>
        <div class="layout">
          <div class="stack">
            <NCard :title="t('reservations.items')" size="small">
              <NDataTable
                size="small"
                :columns="columns"
                :data="reservation.items"
                :bordered="false"
              />
            </NCard>
            <ReservationHistory :reservation="reservation" />
          </div>
          <!-- First on narrow screens: how and when the devices come matters most. -->
          <div class="stack side">
            <HandoverCard
              v-if="reservation.handover"
              :reservation="reservation"
              :printable="false"
            />
            <HandoverPlanCard
              v-else-if="
                ['confirmed', 'ready'].includes(reservation.status) && handoverPlanned(reservation)
              "
              :reservation="reservation"
              for-employee
            />
            <ReturnsCard
              v-if="showReturns"
              :reservation="reservation"
              with-due
              :printable="false"
            />
            <RequestInfoCard :reservation="reservation" />
            <ApprovalCard v-if="reservation.approval" :reservation="reservation" />
          </div>
        </div>
      </div>
    </template>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(300px, 1fr);
  gap: 16px;
  align-items: start;
}
@media (max-width: 1100px) {
  .layout {
    grid-template-columns: 1fr;
  }
}
@media (max-width: 1100px) {
  .side {
    order: -1;
  }
}
:deep(.reduced) {
  color: var(--ar-warning);
  font-weight: 600;
}
</style>
