<script setup lang="ts">
import type { Id } from '@/types/common'
import {
  Ban,
  CalendarClock,
  CalendarPlus,
  Check,
  EllipsisVertical,
  Mail,
  PackageCheck,
  PackageOpen,
  ShoppingCart,
  Sparkles,
  Undo2,
  UserCheck,
  X,
} from '@lucide/vue'
import {
  NAlert,
  NButton,
  NCard,
  NDropdown,
  NInput,
  NModal,
  NSkeleton,
  useMessage,
  type DropdownOption,
} from 'naive-ui'
import { computed, h, onMounted, ref, type Component } from 'vue'
import { useI18n } from 'vue-i18n'

import { portalApi, reservationsApi } from '@/api/reservations'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import CreateOrderModal, { type DraftLine } from '@/components/procurement/CreateOrderModal.vue'
import AllocationPanel from '@/components/reservations/AllocationPanel.vue'
import ConfirmModal from '@/components/reservations/ConfirmModal.vue'
import AssignmentCard from '@/components/reservations/AssignmentCard.vue'
import ExtendModal from '@/components/reservations/ExtendModal.vue'
import HandoverCard from '@/components/reservations/HandoverCard.vue'
import HandOutModal from '@/components/reservations/HandOutModal.vue'
import ReadyModal from '@/components/reservations/ReadyModal.vue'
import ReservationInfo from '@/components/reservations/ReservationInfo.vue'
import ReservationSteps from '@/components/reservations/ReservationSteps.vue'
import ReturnModal from '@/components/reservations/ReturnModal.vue'
import ReturnsCard from '@/components/reservations/ReturnsCard.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import type {
  AvailabilityCounts,
  PeriodAvailability,
  Reservation,
  ReservationItem,
} from '@/types/reservations'
import { isReturnable } from '@/utils/reservations'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ id: Id }>()
const { t } = useI18n()
// Without the right to change reservations, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('reservations', 'write'))
const message = useMessage()
const confirm = useConfirm()
const { busy, run } = useAction()
const { date, dateTime } = useFormat()

const reservation = ref<Reservation | null>(null)
const confirmMode = ref<'confirm' | 'schedule'>('confirm')
const showConfirm = ref(false)
const showReject = ref(false)
const rejectReason = ref('')
const showOrder = ref(false)
const showReady = ref(false)
const showHandOut = ref(false)
const showReturn = ref(false)
const showExtend = ref(false)

const availability = ref<PeriodAvailability | null>(null)

onMounted(async () => {
  reservation.value = await reservationsApi.get(props.id)
  if (reservation.value.status === 'submitted') await loadAvailability(reservation.value)
})

/** Before confirming: what the pool holds in the request's period, from the pickup day on. */
async function loadAvailability(r: Reservation) {
  const pickup = r.requested_pickup_date
  const start = pickup && pickup < r.start_date ? pickup : r.start_date
  availability.value = await portalApi.availability(
    r.duration === 'permanent'
      ? { start, permanent: true }
      : { start, ...(r.end_date ? { end: r.end_date } : {}) },
  )
}

function itemAvailability(item: ReservationItem): AvailabilityCounts | null {
  if (status.value !== 'submitted' || !availability.value || item.is_free_text) return null
  if (item.asset_model) return availability.value.models[item.asset_model.id] ?? null
  if (item.category) return availability.value.categories[item.category.id] ?? null
  return null
}

const status = computed(() => reservation.value?.status)
const missing = computed(() => reservation.value?.items.some((i) => i.quantity_missing) ?? false)
const preparing = computed(() => status.value === 'confirmed')
/** Only license seats: nothing to collect, so marking ready hands it out right away. */
const seatsOnly = computed(() => {
  const allocations = (reservation.value?.items ?? []).flatMap((i) => i.allocations)
  return allocations.length > 0 && allocations.every((a) => a.license)
})

async function markReady() {
  if (!seatsOnly.value) {
    showReady.value = true
    return
  }
  if (await confirm(t('reservations.actions.confirmSeatsOnly'))) {
    await act(
      () =>
        reservationsApi.markReady(props.id, {
          handover_mode: reservation.value!.handover_mode,
          skip_device_check: false,
          pickup_at: reservation.value!.pickup_at,
          pickup_location: reservation.value!.pickup_location?.id ?? null,
        }),
      t('common.saved'),
    )
  }
}

/** Devices or seats still with the employee, also after a permanent hand-out. */
const lent = computed(
  () =>
    ['handed_out', 'completed'].includes(status.value ?? '') &&
    (reservation.value?.items ?? []).some((i) =>
      i.allocations.some((a) => isReturnable(a) && a.handed_out_at && !a.returned_at),
    ),
)

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

function openConfirm(mode: 'confirm' | 'schedule') {
  confirmMode.value = mode
  showConfirm.value = true
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

async function reopen() {
  if (await confirm(t('reservations.actions.confirmReopen'))) {
    await act(() => reservationsApi.reopen(props.id), t('common.saved'))
  }
}

const canRemind = computed(
  () => status.value === 'handed_out' && reservation.value?.duration === 'temporary',
)

async function remind() {
  const name = reservation.value!.requester.display_name
  if (await confirm(t('reservations.actions.confirmRemind', { name }))) {
    await act(
      () => reservationsApi.remind(props.id),
      t('reservations.actions.remindSent', { name }),
    )
  }
}

/** Rare actions, kept out of the header so the next step stands out. */
const menuOptions = computed<DropdownOption[]>(() => {
  const option = (key: string, label: string, icon: Component, danger = false) => ({
    key,
    label,
    icon: () => h(icon, { size: 15 }),
    props: danger ? { style: 'color: var(--ar-error)' } : undefined,
  })
  const s = status.value
  const options: DropdownOption[] = []
  if (s === 'submitted' && missing.value)
    options.push(option('order', t('reservations.actions.createOrder'), ShoppingCart))
  if (s === 'ready') {
    // While preparing, "Edit" covers date and place; once ready this is the way to change them.
    options.push(option('schedule', t('reservations.actions.schedule'), CalendarClock))
    options.push(option('reopen', t('reservations.actions.reopen'), PackageOpen))
  }
  // Overdue, the alert offers it.
  if (canRemind.value && !reservation.value?.is_overdue)
    options.push(option('remind', t('reservations.actions.remind'), Mail))
  if (['pending_approval', 'submitted', 'confirmed', 'ready'].includes(s ?? '')) {
    if (options.length) options.push({ type: 'divider', key: 'cancel-divider' })
    options.push(option('cancel', t('reservations.actions.cancel'), Ban, true))
  }
  return options
})

function onMenu(key: string) {
  if (key === 'order') showOrder.value = true
  else if (key === 'schedule') openConfirm('schedule')
  else if (key === 'reopen') reopen()
  else if (key === 'cancel') cancel()
  else if (key === 'remind') remind()
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
        <template v-if="canWrite" #actions>
          <template v-if="status === 'submitted'">
            <NButton @click="showReject = true">
              <template #icon><X :size="15" /></template>
              {{ t('reservations.actions.reject') }}
            </NButton>
            <NButton type="primary" @click="openConfirm('confirm')">
              <template #icon><Check :size="15" /></template>
              {{ t('reservations.actions.confirm') }}
            </NButton>
          </template>
          <template v-if="status === 'confirmed'">
            <NButton @click="openConfirm('confirm')">{{ t('common.edit') }}</NButton>
            <NButton v-if="missing" :loading="busy" @click="autoAllocate">
              <template #icon><Sparkles :size="15" /></template>
              {{ t('reservations.actions.autoAllocate') }}
            </NButton>
            <NButton type="primary" :disabled="missing" :loading="busy" @click="markReady">
              <template #icon><PackageCheck :size="15" /></template>
              {{
                seatsOnly
                  ? t('reservations.actions.completeSeats')
                  : t('reservations.actions.markReady')
              }}
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
          <NButton
            v-if="status === 'handed_out' && reservation.duration === 'temporary'"
            @click="showExtend = true"
          >
            <template #icon><CalendarPlus :size="15" /></template>
            {{ t('reservations.actions.extend') }}
          </NButton>
          <NButton
            v-if="lent"
            :type="status === 'handed_out' ? 'primary' : 'default'"
            @click="showReturn = true"
          >
            <template #icon><Undo2 :size="15" /></template>
            {{ t('reservations.actions.return') }}
          </NButton>
          <NButton v-if="status === 'confirmed' && missing" @click="showOrder = true">
            <template #icon><ShoppingCart :size="15" /></template>
            {{ t('reservations.actions.createOrder') }}
          </NButton>
          <NDropdown
            v-if="menuOptions.length"
            trigger="click"
            placement="bottom-end"
            :options="menuOptions"
            @select="onMenu"
          >
            <NButton :title="t('reservations.moreActions')">
              <template #icon><EllipsisVertical :size="16" /></template>
            </NButton>
          </NDropdown>
        </template>
      </PageHeader>

      <div class="stack">
        <NAlert v-if="status === 'pending_approval'" type="info" :bordered="false">
          {{ t('reservations.approval.itWaiting') }}
        </NAlert>
        <NAlert
          v-if="reservation.is_overdue && reservation.end_date"
          type="error"
          :title="t('reservations.overdueAlert.title', { date: date(reservation.end_date) })"
        >
          <div class="overdue">
            <span>
              {{
                t('reservations.overdueAlert.text', { name: reservation.requester.display_name })
              }}
              <template v-if="reservation.reminded_at">
                {{
                  t('reservations.overdueAlert.reminded', {
                    date: dateTime(reservation.reminded_at),
                    name: reservation.reminded_by?.display_name ?? '—',
                  })
                }}
              </template>
            </span>
            <NButton size="small" :loading="busy" @click="remind">
              <template #icon><Mail :size="14" /></template>
              {{ t('reservations.actions.remind') }}
            </NButton>
          </div>
        </NAlert>
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
              :availability="itemAvailability(item)"
              @updated="(r) => (reservation = r)"
            />
          </NCard>
          <div class="stack">
            <AssignmentCard :reservation="reservation" @updated="(r) => (reservation = r)" />
            <!-- How the devices get to the employee, while that is still ahead. -->
            <NAlert
              v-if="status === 'ready'"
              type="info"
              :bordered="false"
              :title="t(`handover.mode.${reservation.handover_mode}`)"
            >
              <template v-if="reservation.handover_mode === 'pickup'">
                {{ t('handover.waitingAtTerminal') }}
                <template v-if="reservation.skip_device_check">
                  {{ t('handover.checkSkipped') }}</template
                >
              </template>
              <template v-else-if="reservation.handover_mode === 'collect'">{{
                t('handover.collectPending')
              }}</template>
              <template v-else>{{ t('handover.deliveryPending') }}</template>
            </NAlert>
            <HandoverCard v-if="reservation.handover" :reservation="reservation" />
            <ReturnsCard v-if="reservation.returns.length" :reservation="reservation" />
            <NCard size="small"><ReservationInfo :reservation="reservation" /></NCard>
          </div>
        </div>
      </div>

      <ConfirmModal
        v-model:show="showConfirm"
        :reservation="reservation"
        :mode="confirmMode"
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
      <ExtendModal
        v-model:show="showExtend"
        :reservation="reservation"
        @saved="(r) => (reservation = r)"
      />
      <ReturnModal
        v-model:show="showReturn"
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
.overdue {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 16px;
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
