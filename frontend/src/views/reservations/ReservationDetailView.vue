<script setup lang="ts">
import type { Id } from '@/types/common'
import {
  CalendarClock,
  Check,
  PackageCheck,
  ShoppingCart,
  Sparkles,
  Undo2,
  UserCheck,
  X,
} from '@lucide/vue'
import { NAlert, NButton, NCard, NInput, NModal, NSkeleton, useMessage } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { reservationsApi } from '@/api/reservations'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import CreateOrderModal, { type DraftLine } from '@/components/procurement/CreateOrderModal.vue'
import AllocationPanel from '@/components/reservations/AllocationPanel.vue'
import ApproveModal from '@/components/reservations/ApproveModal.vue'
import HandoverCard from '@/components/reservations/HandoverCard.vue'
import HandOutModal from '@/components/reservations/HandOutModal.vue'
import ReadyModal from '@/components/reservations/ReadyModal.vue'
import ReservationInfo from '@/components/reservations/ReservationInfo.vue'
import ReservationSteps from '@/components/reservations/ReservationSteps.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import type { Reservation } from '@/types/reservations'

const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const message = useMessage()
const confirm = useConfirm()
const { busy, run } = useAction()

const reservation = ref<Reservation | null>(null)
const approveMode = ref<'approve' | 'schedule'>('approve')
const showApprove = ref(false)
const showReject = ref(false)
const rejectReason = ref('')
const showOrder = ref(false)
const showReady = ref(false)
const showHandOut = ref(false)

onMounted(async () => (reservation.value = await reservationsApi.get(props.id)))

const status = computed(() => reservation.value?.status)
const missing = computed(() => reservation.value?.items.some((i) => i.quantity_missing) ?? false)
const preparing = computed(() => status.value === 'approved')

const orderLines = computed<DraftLine[]>(() =>
  (reservation.value?.items ?? [])
    .filter((i) => i.quantity_missing)
    .map((i) => ({
      label: i.label,
      asset_model: i.asset_model?.id ?? null,
      category: i.category?.id ?? null,
      quantity: i.quantity_missing,
      reservation_item: i.id,
    })),
)

async function act(action: () => Promise<Reservation>, success?: string) {
  const updated = await run(action, success)
  if (updated) reservation.value = updated
}

function openApprove(mode: 'approve' | 'schedule') {
  approveMode.value = mode
  showApprove.value = true
}

async function autoAllocate() {
  const result = await run(() => reservationsApi.autoAllocate(props.id))
  if (result) {
    reservation.value = result.reservation
    message.info(t('reservations.actions.autoAllocated', { count: result.allocated }))
  }
}

async function reject() {
  await act(() => reservationsApi.reject(props.id, rejectReason.value))
  showReject.value = false
}

async function returnAll() {
  if (await confirm(t('reservations.actions.confirmReturn'))) {
    await act(() => reservationsApi.returnDevices(props.id), t('common.saved'))
  }
}

async function cancel() {
  if (await confirm(t('reservations.actions.confirmCancel'), { danger: true })) {
    await act(() => reservationsApi.cancel(props.id))
  }
}
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!reservation" height="240px" />
    <template v-else>
      <PageHeader :title="reservation.title">
        <template #eyebrow
          ><span class="mono id">{{ reservation.number }}</span></template
        >
        <template #badge
          ><StatusTag group="reservationStatus" :value="reservation.status"
        /></template>
        <template #actions>
          <template v-if="status === 'submitted'">
            <NButton @click="showReject = true">
              <template #icon><X :size="15" /></template>
              {{ t('reservations.actions.reject') }}
            </NButton>
            <NButton type="primary" @click="openApprove('approve')">
              <template #icon><Check :size="15" /></template>
              {{ t('reservations.actions.approve') }}
            </NButton>
          </template>
          <template v-if="status === 'approved'">
            <NButton @click="openApprove('approve')">{{ t('common.edit') }}</NButton>
            <NButton v-if="missing" :loading="busy" @click="autoAllocate">
              <template #icon><Sparkles :size="15" /></template>
              {{ t('reservations.actions.autoAllocate') }}
            </NButton>
            <NButton type="primary" :disabled="missing" :loading="busy" @click="showReady = true">
              <template #icon><PackageCheck :size="15" /></template>
              {{ t('reservations.actions.markReady') }}
            </NButton>
          </template>
          <template v-if="status === 'approved' || status === 'ready'">
            <NButton @click="openApprove('schedule')">
              <template #icon><CalendarClock :size="15" /></template>
              {{ t('reservations.actions.schedule') }}
            </NButton>
          </template>
          <NButton
            v-if="status === 'ready'"
            :type="reservation.handover_mode === 'pickup' ? 'default' : 'primary'"
            @click="showHandOut = true"
          >
            <template #icon><UserCheck :size="15" /></template>
            {{ t('reservations.actions.handOut') }}
          </NButton>
          <NButton v-if="status === 'handed_out'" type="primary" :loading="busy" @click="returnAll">
            <template #icon><Undo2 :size="15" /></template>
            {{ t('reservations.actions.return') }}
          </NButton>
          <NButton
            v-if="['submitted', 'approved'].includes(status!) && missing"
            @click="showOrder = true"
          >
            <template #icon><ShoppingCart :size="15" /></template>
            {{ t('reservations.actions.createOrder') }}
          </NButton>
          <NButton
            v-if="['submitted', 'approved', 'ready'].includes(status!)"
            quaternary
            type="error"
            @click="cancel"
          >
            {{ t('reservations.actions.cancel') }}
          </NButton>
        </template>
      </PageHeader>

      <div class="stack">
        <NCard size="small"><ReservationSteps :reservation="reservation" /></NCard>
        <div class="layout">
          <NCard
            :title="preparing ? t('reservations.allocation.title') : t('reservations.items')"
            size="small"
          >
            <p v-if="preparing" class="muted small hint">{{ t('reservations.allocation.hint') }}</p>
            <AllocationPanel
              v-for="item in reservation.items"
              :key="item.id"
              :reservation="reservation"
              :item="item"
              :editable="preparing"
              @updated="(r) => (reservation = r)"
            />
          </NCard>
          <div class="stack">
            <NAlert
              v-if="status === 'ready' && reservation.handover_mode === 'pickup'"
              type="info"
              :bordered="false"
            >
              {{ t('handover.waitingAtTerminal') }}
            </NAlert>
            <HandoverCard v-if="reservation.handover" :reservation="reservation" />
            <NCard size="small"><ReservationInfo :reservation="reservation" /></NCard>
          </div>
        </div>
      </div>

      <ApproveModal
        v-model:show="showApprove"
        :reservation="reservation"
        :mode="approveMode"
        @saved="(r) => (reservation = r)"
      />
      <CreateOrderModal v-model:show="showOrder" :lines="orderLines" />
      <ReadyModal
        v-model:show="showReady"
        :reservation="reservation"
        @saved="(r) => (reservation = r)"
      />
      <HandOutModal
        v-model:show="showHandOut"
        :reservation="reservation"
        @saved="(r) => (reservation = r)"
      />
      <NModal
        v-model:show="showReject"
        preset="card"
        :title="t('reservations.actions.reject')"
        style="max-width: 460px"
      >
        <NInput
          v-model:value="rejectReason"
          type="textarea"
          :placeholder="t('reservations.actions.rejectReason')"
          :autosize="{ minRows: 3 }"
        />
        <template #footer>
          <div class="row" style="justify-content: flex-end">
            <NButton @click="showReject = false">{{ t('common.cancel') }}</NButton>
            <NButton
              type="error"
              :disabled="!rejectReason.trim()"
              :loading="busy"
              @click="reject"
              >{{ t('reservations.actions.reject') }}</NButton
            >
          </div>
        </template>
      </NModal>
    </template>
  </div>
</template>

<style scoped>
.id {
  font-size: 12px;
  color: var(--ar-primary);
}
.small {
  font-size: 11.5px;
}
.hint {
  margin: -4px 0 4px;
}
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
</style>
