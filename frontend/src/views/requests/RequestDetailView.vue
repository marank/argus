<script setup lang="ts">
import { useLive } from '@/composables/useLive'
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
  type DropdownOption,
} from 'naive-ui'
import { computed, h, onMounted, ref, type Component } from 'vue'
import { useI18n } from 'vue-i18n'

import { portalApi, requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import PageHeader from '@/components/common/PageHeader.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import CreateOrderModal, { type DraftLine } from '@/components/procurement/CreateOrderModal.vue'
import AllocationPanel from '@/components/requests/AllocationPanel.vue'
import ConfirmModal from '@/components/requests/ConfirmModal.vue'
import AssignmentCard from '@/components/requests/AssignmentCard.vue'
import ExtendModal from '@/components/requests/ExtendModal.vue'
import HandoverCard from '@/components/requests/HandoverCard.vue'
import HandOutModal from '@/components/requests/HandOutModal.vue'
import ReadyModal from '@/components/requests/ReadyModal.vue'
import RequestSteps from '@/components/requests/RequestSteps.vue'
import ReturnModal from '@/components/requests/ReturnModal.vue'
import OriginTag from '@/components/requests/OriginTag.vue'
import ReturnsCard from '@/components/requests/ReturnsCard.vue'
import ApprovalCard from '@/components/requests/detail/ApprovalCard.vue'
import HandoverPlanCard from '@/components/requests/detail/HandoverPlanCard.vue'
import RequestInfoCard from '@/components/requests/detail/RequestInfoCard.vue'
import RequestHistory from '@/components/requests/detail/RequestHistory.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import { handoverPlanned, isReturnable, itemLabel } from '@/utils/requests'
import { useAuthStore } from '@/stores/auth'

const props = defineProps<{ id: Id }>()
const { t } = useI18n()
// Without the right to change requests, the page is for viewing only.
const canWrite = computed(() => useAuthStore().can('requests', 'write'))
const confirm = useConfirm()
const { busy, run } = useAction()
const { date, dateTime } = useFormat()

const assetRequest = ref<Schemas['AssetRequestOut'] | null>(null)
const confirmMode = ref<'confirm' | 'schedule'>('confirm')
const showConfirm = ref(false)
const showReject = ref(false)
const rejectReason = ref('')
const showOrder = ref(false)
const showReady = ref(false)
const showHandOut = ref(false)
const showReturn = ref(false)
const showExtend = ref(false)

const availability = ref<Schemas['AvailabilityOut'] | null>(null)

async function load() {
  assetRequest.value = await requestsApi.get(props.id)
  if (assetRequest.value.status === 'submitted') await loadAvailability(assetRequest.value)
}
onMounted(load)
// A colleague's step shows up right away, but not underneath an open dialog.
useLive(['request'], load, {
  id: () => props.id,
  paused: () =>
    showConfirm.value ||
    showReject.value ||
    showOrder.value ||
    showReady.value ||
    showHandOut.value ||
    showReturn.value ||
    showExtend.value,
})

/** Before confirming: what the pool holds in the request's period, from the pickup day on. */
async function loadAvailability(r: Schemas['AssetRequestOut']) {
  const pickup = r.requested_pickup_date
  const start = pickup && pickup < r.start_date ? pickup : r.start_date
  availability.value = await portalApi.availability(
    r.duration === 'permanent'
      ? { start, permanent: true }
      : { start, ...(r.end_date ? { end: r.end_date } : {}) },
  )
}

function itemAvailability(item: Schemas['AssetRequestItemOut']): Schemas['CountsOut'] | null {
  if (status.value !== 'submitted' || !availability.value || item.is_free_text) return null
  if (item.asset_model) return availability.value.models[item.asset_model.id] ?? null
  if (item.category) return availability.value.categories[item.category.id] ?? null
  return null
}

const status = computed(() => assetRequest.value?.status)
const missing = computed(() => assetRequest.value?.items.some((i) => i.quantity_missing) ?? false)
const preparing = computed(() => status.value === 'confirmed')
/** Handed out without recorded devices: they can still be recorded. */
const recording = computed(
  () =>
    !!assetRequest.value?.devices_unrecorded &&
    ['handed_out', 'completed'].includes(status.value ?? ''),
)
/** The lines without devices, e.g. "2× ThinkPad T14". */
const missingLines = computed(() =>
  (assetRequest.value?.items ?? [])
    .filter((i) => i.quantity_missing)
    .map((i) => `${i.quantity_missing}× ${itemLabel(i)}`)
    .join(', '),
)

/** The devices went out outside the system before the request was prepared. */
async function handOutUnrecorded() {
  if (await confirm(t('requests.unrecorded.confirmHandOut', { items: missingLines.value }))) {
    await act(() => requestsApi.handOutUnrecorded(props.id))
  }
}

async function returnUnrecorded() {
  if (await confirm(t('requests.unrecorded.confirmReturn', { items: missingLines.value }))) {
    await act(() => requestsApi.returnUnrecorded(props.id))
  }
}
/** Only license seats: nothing to collect, so marking ready hands it out right away. */
const seatsOnly = computed(() => {
  const allocations = (assetRequest.value?.items ?? []).flatMap((i) => i.allocations)
  return allocations.length > 0 && allocations.every((a) => a.license)
})

async function markReady() {
  if (!seatsOnly.value) {
    showReady.value = true
    return
  }
  if (await confirm(t('requests.actions.confirmSeatsOnly'))) {
    await act(() =>
      requestsApi.markReady(props.id, {
        handover_mode: assetRequest.value!.handover_mode,
        skip_device_check: false,
        pickup_at: assetRequest.value!.pickup_at,
        pickup_location: assetRequest.value!.pickup_location?.id ?? null,
        notify: true,
      }),
    )
  }
}

/** Devices or seats still with the employee, also after a permanent hand-out. */
const lent = computed(
  () =>
    ['handed_out', 'completed'].includes(status.value ?? '') &&
    (assetRequest.value?.items ?? []).some((i) =>
      i.allocations.some((a) => isReturnable(a) && a.handed_out_at && !a.returned_at),
    ),
)

const orderLines = computed<DraftLine[]>(() =>
  (assetRequest.value?.items ?? [])
    .filter((i) => i.quantity_missing)
    .map((i) => ({
      label: i.label,
      asset_model: i.asset_model?.id ?? null,
      category: i.category?.id ?? null,
      quantity: i.quantity_missing,
      asset_request_item: i.id,
    })),
)

/** Runs an action on the request and shows its result; false when it failed. */
async function act(
  action: () => Promise<Schemas['AssetRequestOut']>,
  success?: string,
): Promise<boolean> {
  const updated = await run(action, success)
  if (updated) assetRequest.value = updated
  return !!updated
}

function openConfirm(mode: 'confirm' | 'schedule') {
  confirmMode.value = mode
  showConfirm.value = true
}

async function reject() {
  // Stays open when it fails (e.g. a colleague confirmed meanwhile), like every dialog here.
  if (await act(() => requestsApi.reject(props.id, rejectReason.value))) showReject.value = false
}

async function reopen() {
  if (await confirm(t('requests.actions.confirmReopen'))) {
    await act(() => requestsApi.reopen(props.id))
  }
}

/** The return tile: due date and reminders while lent, then what came back. */
const showReturns = computed(
  () =>
    (assetRequest.value?.returns.length ?? 0) > 0 ||
    (assetRequest.value?.duration === 'temporary' &&
      ['handed_out', 'completed'].includes(status.value ?? '') &&
      Boolean(assetRequest.value?.handover)),
)

/** What is up next, shown above the cards. Overdue loans have their own alert. */
const nextStep = computed(() => {
  const r = assetRequest.value
  if (!r) return null
  const name = r.requester.display_name
  switch (r.status) {
    case 'pending_approval':
      return t('requests.nextStep.pendingApproval')
    case 'submitted':
      return t('requests.nextStep.submitted')
    case 'confirmed':
      if (missing.value) return t('requests.nextStep.allocate')
      return t(seatsOnly.value ? 'requests.nextStep.completeSeats' : 'requests.nextStep.markReady')
    case 'ready':
      return t(
        r.handover_mode === 'pickup' ? 'requests.nextStep.pickup' : 'requests.nextStep.handOut',
        {
          name,
        },
      )
    case 'handed_out':
      if (r.devices_unrecorded) return t('requests.nextStep.unrecorded')
      if (r.duration !== 'temporary' || r.is_overdue || !r.end_date) return null
      return t('requests.nextStep.lent', { date: date(r.end_date) })
    case 'completed':
      return r.devices_unrecorded ? t('requests.nextStep.unrecordedPermanent') : null
    default:
      return null
  }
})

const canRemind = computed(
  () => status.value === 'handed_out' && assetRequest.value?.duration === 'temporary',
)

async function remind() {
  const name = assetRequest.value!.requester.display_name
  if (await confirm(t('requests.actions.confirmRemind', { name }))) {
    await act(() => requestsApi.remind(props.id), t('requests.actions.remindSent', { name }))
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
    options.push(option('order', t('requests.actions.createOrder'), ShoppingCart))
  if (s === 'ready') {
    // How, when and where is set when marking ready; this changes it afterwards.
    options.push(option('schedule', t('requests.actions.schedule'), CalendarClock))
    options.push(option('reopen', t('requests.actions.reopen'), PackageOpen))
  }
  // Overdue, the alert offers it.
  if (canRemind.value && !assetRequest.value?.is_overdue)
    options.push(option('remind', t('requests.actions.remind'), Mail))
  if (['pending_approval', 'submitted', 'confirmed', 'ready'].includes(s ?? '')) {
    if (options.length) options.push({ type: 'divider', key: 'cancel-divider' })
    options.push(option('cancel', t('requests.actions.cancel'), Ban, true))
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
  if (await confirm(t('requests.actions.confirmCancel'), { danger: true })) {
    await act(() => requestsApi.cancel(props.id))
  }
}
</script>

<template>
  <div class="page">
    <NSkeleton v-if="!assetRequest" height="240px" />
    <template v-else>
      <PageHeader :title="assetRequest.title">
        <template #eyebrow
          ><span class="mono id">{{ assetRequest.number }}</span></template
        >
        <template #badge
          ><StatusTag group="requestStatus" :value="assetRequest.status" /><OriginTag
            :origin="assetRequest.origin"
        /></template>
        <template v-if="canWrite" #actions>
          <template v-if="status === 'submitted'">
            <NButton @click="showReject = true">
              <template #icon><X :size="15" /></template>
              {{ t('requests.actions.reject') }}
            </NButton>
            <NButton type="primary" @click="openConfirm('confirm')">
              <template #icon><Check :size="15" /></template>
              {{ t('requests.actions.confirm') }}
            </NButton>
          </template>
          <template v-if="status === 'confirmed'">
            <NButton @click="openConfirm('confirm')">{{ t('common.edit') }}</NButton>
            <!-- Ready only once everything confirmed is allocated. -->
            <NButton v-if="missing" :loading="busy" @click="handOutUnrecorded">
              {{ t('requests.actions.handOutUnrecorded') }}
            </NButton>
            <NButton v-if="!missing" type="primary" :loading="busy" @click="markReady">
              <template #icon><PackageCheck :size="15" /></template>
              {{
                seatsOnly ? t('requests.actions.completeSeats') : t('requests.actions.markReady')
              }}
            </NButton>
          </template>
          <NButton
            v-if="status === 'ready'"
            :type="assetRequest.handover_mode === 'pickup' ? 'default' : 'primary'"
            @click="showHandOut = true"
          >
            <template #icon><UserCheck :size="15" /></template>
            {{ t('requests.actions.handOut') }}
          </NButton>
          <NButton
            v-if="status === 'handed_out' && assetRequest.duration === 'temporary'"
            @click="showExtend = true"
          >
            <template #icon><CalendarPlus :size="15" /></template>
            {{ t('requests.actions.extend') }}
          </NButton>
          <NButton
            v-if="lent"
            :type="status === 'handed_out' ? 'primary' : 'default'"
            @click="showReturn = true"
          >
            <template #icon><Undo2 :size="15" /></template>
            {{ t('requests.actions.return') }}
          </NButton>
          <NButton
            v-if="status === 'handed_out' && assetRequest.devices_unrecorded"
            :type="lent ? 'default' : 'primary'"
            :loading="busy"
            @click="returnUnrecorded"
          >
            {{ t('requests.actions.returnUnrecorded') }}
          </NButton>
          <NButton v-if="status === 'confirmed' && missing" @click="showOrder = true">
            <template #icon><ShoppingCart :size="15" /></template>
            {{ t('requests.actions.createOrder') }}
          </NButton>
          <NDropdown
            v-if="menuOptions.length"
            trigger="click"
            placement="bottom-end"
            :options="menuOptions"
            @select="onMenu"
          >
            <NButton :title="t('requests.moreActions')">
              <template #icon><EllipsisVertical :size="16" /></template>
            </NButton>
          </NDropdown>
        </template>
      </PageHeader>

      <div class="stack">
        <NCard size="small"><RequestSteps :assetRequest="assetRequest" /></NCard>
        <NAlert v-if="nextStep" type="info" :bordered="false" :title="t('requests.nextStep.title')">
          {{ nextStep }}
        </NAlert>
        <NAlert
          v-if="assetRequest.is_overdue && assetRequest.end_date"
          type="error"
          :title="t('requests.overdueAlert.title', { date: date(assetRequest.end_date) })"
        >
          <div class="overdue">
            <span>
              {{ t('requests.overdueAlert.text', { name: assetRequest.requester.display_name }) }}
              <template v-if="assetRequest.reminded_at">
                {{
                  t('requests.overdueAlert.reminded', {
                    date: dateTime(assetRequest.reminded_at),
                    name: assetRequest.reminded_by?.display_name ?? '—',
                  })
                }}
              </template>
            </span>
            <NButton size="small" :loading="busy" @click="remind">
              <template #icon><Mail :size="14" /></template>
              {{ t('requests.actions.remind') }}
            </NButton>
          </div>
        </NAlert>
        <div class="layout">
          <div class="stack">
            <NCard
              :title="
                preparing
                  ? t('requests.allocation.title')
                  : recording
                    ? t('requests.unrecorded.title')
                    : t('requests.items')
              "
              size="small"
            >
              <p v-if="preparing || recording" class="muted small hint">
                {{ t(recording ? 'requests.unrecorded.hint' : 'requests.allocation.hint') }}
              </p>
              <AllocationPanel
                v-for="item in assetRequest.items"
                :key="item.id"
                :assetRequest="assetRequest"
                :item="item"
                :editable="preparing || recording"
                :availability="itemAvailability(item)"
                @updated="(r) => (assetRequest = r)"
              />
            </NCard>
            <RequestHistory :assetRequest="assetRequest" />
          </div>
          <div class="stack">
            <AssignmentCard :assetRequest="assetRequest" @updated="(r) => (assetRequest = r)" />
            <RequestInfoCard :assetRequest="assetRequest" />
            <ApprovalCard v-if="assetRequest.approval" :assetRequest="assetRequest" />
            <HandoverCard v-if="assetRequest.handover" :assetRequest="assetRequest" />
            <HandoverPlanCard
              v-else-if="
                ['confirmed', 'ready'].includes(assetRequest.status) &&
                handoverPlanned(assetRequest)
              "
              :assetRequest="assetRequest"
            />
            <ReturnsCard v-if="showReturns" :assetRequest="assetRequest" with-due />
          </div>
        </div>
      </div>

      <ConfirmModal
        v-model:show="showConfirm"
        :assetRequest="assetRequest"
        :mode="confirmMode"
        @saved="(r) => (assetRequest = r)"
      />
      <CreateOrderModal v-model:show="showOrder" :lines="orderLines" />
      <ReadyModal
        v-model:show="showReady"
        :assetRequest="assetRequest"
        @saved="(r) => (assetRequest = r)"
      />
      <HandOutModal
        v-model:show="showHandOut"
        :assetRequest="assetRequest"
        @saved="(r) => (assetRequest = r)"
      />
      <ExtendModal
        v-model:show="showExtend"
        :assetRequest="assetRequest"
        @saved="(r) => (assetRequest = r)"
      />
      <ReturnModal
        v-model:show="showReturn"
        :assetRequest="assetRequest"
        @saved="(r) => (assetRequest = r)"
      />
      <NModal
        v-model:show="showReject"
        preset="card"
        :title="t('requests.actions.reject')"
        style="max-width: 460px"
      >
        <NInput
          v-model:value="rejectReason"
          type="textarea"
          :placeholder="t('requests.actions.rejectReason')"
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
              >{{ t('requests.actions.reject') }}</NButton
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
