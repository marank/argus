<script setup lang="ts">
import type { Id } from '@/types/common'
import { ScanLine, X } from '@lucide/vue'
import { NButton, NInput, NInputNumber, NPopselect, NProgress, NSelect } from 'naive-ui'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { reservationsApi } from '@/api/reservations'
import StatusTag from '@/components/common/StatusTag.vue'
import { useAction } from '@/composables/useAction'
import type {
  AvailabilityCounts,
  Candidates,
  Reservation,
  ReservationItem,
} from '@/types/reservations'
import { itemLabel } from '@/utils/reservations'

import ResolveFreeText from './ResolveFreeText.vue'

/** One reservation item: its allocated devices plus tools to allocate more. */
const props = defineProps<{
  reservation: Reservation
  item: ReservationItem
  editable: boolean
  /** Pool counts for the request's period, shown before IT confirms. */
  availability?: AvailabilityCounts | null
}>()
const emit = defineEmits<{ updated: [reservation: Reservation] }>()
const { t } = useI18n()
const { busy, run } = useAction()

const code = ref('')
const candidates = ref<Candidates | null>(null)
const consumableQuantity = ref(1)
const licenseId = ref<Id | null>(null)
const deviceId = ref<Id | null>(null)

const licenseOptions = computed(() =>
  (candidates.value?.licenses ?? []).map((l) => ({
    value: l.id,
    label: `${l.model.full_name}${l.reference ? ` (${l.reference})` : ''} · ${t('reservations.allocation.freeSeats', { count: l.free_seats })}`,
  })),
)
const chosenLicense = computed(() =>
  candidates.value?.licenses?.find((l) => l.id === licenseId.value),
)
const deviceOptions = computed(() =>
  (candidates.value?.devices ?? []).map((d) => ({
    value: d.id,
    label: `${d.inventory_number} · ${d.model.full_name}`,
  })),
)
const canAssignSeat = computed(
  () =>
    Boolean(chosenLicense.value) &&
    (chosenLicense.value?.assign_to === 'user' || Boolean(deviceId.value)),
)

async function assignSeat() {
  if (!licenseId.value) return
  await allocate({ license: licenseId.value, ...(deviceId.value ? { asset: deviceId.value } : {}) })
  licenseId.value = null
  deviceId.value = null
}

const target = computed(() => props.item.quantity_confirmed ?? props.item.quantity_requested)
const percent = computed(() =>
  target.value ? (props.item.quantity_allocated / target.value) * 100 : 100,
)

const assetOptions = computed(() =>
  (candidates.value?.assets ?? []).map((a) => ({
    value: a.id,
    label: `${a.inventory_number} · ${a.model.full_name}${a.serial_number ? ` · ${a.serial_number}` : ''}`,
  })),
)

async function loadCandidates() {
  candidates.value = await reservationsApi.candidates(props.item.id)
}

async function allocate(data: {
  asset?: Id
  consumable?: Id
  license?: Id
  quantity?: number
  code?: string
}) {
  const updated = await run(() =>
    reservationsApi.allocate(props.reservation.id, { item: props.item.id, ...data }),
  )
  if (updated) {
    code.value = ''
    emit('updated', updated)
    if (candidates.value) await loadCandidates()
  }
}

async function remove(allocationId: Id) {
  const updated = await run(() =>
    reservationsApi.removeAllocation(props.reservation.id, allocationId),
  )
  if (updated) emit('updated', updated)
}
</script>

<template>
  <div class="item">
    <div class="head">
      <div>
        <strong>
          {{ itemLabel(item) }}
          <span v-if="item.is_free_text" class="free-tag">{{ t('reservations.freeText') }}</span>
        </strong>
        <div v-if="item.description && !item.is_free_text" class="muted small">
          {{ t('reservations.freeTextResolve.requested', { text: item.description }) }}
        </div>
        <div v-if="item.note" class="muted small">{{ item.note }}</div>
      </div>
      <div class="counts mono">
        <span :class="{ done: !item.quantity_missing }">{{ item.quantity_allocated }}</span>
        <span class="muted">/ {{ target }}</span>
        <span
          v-if="
            item.quantity_confirmed !== null && item.quantity_confirmed < item.quantity_requested
          "
          class="reduced"
          :title="t('reservations.quantities.requested')"
        >
          ({{ item.quantity_requested }})
        </span>
        <div
          v-if="availability"
          class="availability small"
          :class="availability.available >= target ? 'enough' : 'short'"
          :title="
            availability.reserved
              ? t('reservations.allocation.periodReserved', { count: availability.reserved })
              : undefined
          "
        >
          {{ t('reservations.allocation.periodFree', { count: availability.available }) }}
        </div>
      </div>
    </div>
    <NProgress
      type="line"
      :percentage="percent"
      :show-indicator="false"
      :height="3"
      :status="item.quantity_missing ? 'default' : 'success'"
    />

    <ResolveFreeText
      v-if="item.is_free_text && ['submitted', 'confirmed'].includes(reservation.status)"
      :reservation="reservation"
      :item="item"
      @updated="(r) => emit('updated', r)"
    />

    <ul class="allocations">
      <li v-for="allocation in item.allocations" :key="allocation.id">
        <template v-if="allocation.asset">
          <RouterLink :to="{ name: 'asset', params: { id: allocation.asset.id } }" class="mono">{{
            allocation.asset.inventory_number
          }}</RouterLink>
          <span>{{ allocation.asset.model.full_name }}</span>
          <span class="mono muted">{{ allocation.asset.serial_number }}</span>
        </template>
        <template v-else-if="allocation.license">
          <RouterLink
            :to="{ name: 'license', params: { id: allocation.license.id } }"
            class="mono"
            >{{ t('reservations.allocation.seat') }}</RouterLink
          >
          <span>{{ allocation.license.model.full_name }}</span>
          <span class="mono muted">{{
            allocation.license.device
              ? allocation.license.device.inventory_number
              : reservation.requester.display_name
          }}</span>
        </template>
        <template v-else-if="allocation.consumable">
          <span class="mono">{{ allocation.quantity }}×</span>
          <span>{{ allocation.consumable.model.full_name }}</span>
          <span class="muted">{{
            t('reservations.allocation.consumableFrom', {
              location: allocation.consumable.location.name,
            })
          }}</span>
        </template>
        <span v-if="allocation.handout_note" class="note" :title="allocation.handout_note">{{
          allocation.handout_note
        }}</span>
        <span class="state">
          <StatusTag
            v-if="allocation.returned_at"
            group="assetStatus"
            :value="allocation.returned_damaged ? 'in_repair' : 'in_stock'"
          />
          <span v-else-if="allocation.handed_out_at" class="muted small">{{
            t('reservations.allocation.handedOut')
          }}</span>
          <NButton
            v-else-if="editable || reservation.status === 'ready'"
            quaternary
            size="tiny"
            :title="t('common.remove')"
            @click="remove(allocation.id)"
          >
            <template #icon><X :size="13" /></template>
          </NButton>
        </span>
      </li>
    </ul>

    <div v-if="editable && item.quantity_missing && item.is_software" class="tools">
      <NSelect
        v-model:value="licenseId"
        size="small"
        :options="licenseOptions"
        :placeholder="t('reservations.allocation.chooseLicense')"
        class="pick"
        @focus="!candidates && loadCandidates()"
      />
      <NSelect
        v-if="chosenLicense?.assign_to === 'device'"
        v-model:value="deviceId"
        size="small"
        :options="deviceOptions"
        :placeholder="t('reservations.allocation.chooseDevice')"
        class="pick"
      />
      <NButton size="small" :disabled="!canAssignSeat" :loading="busy" @click="assignSeat">{{
        t('reservations.allocation.assignSeat')
      }}</NButton>
      <span v-if="candidates && !licenseOptions.length" class="muted small">
        {{ t('reservations.allocation.noSeats') }}
        <RouterLink :to="{ name: 'licenses' }">{{
          t('reservations.allocation.toLicenses')
        }}</RouterLink>
      </span>
    </div>

    <div
      v-if="editable && item.quantity_missing && !item.is_free_text && !item.is_software"
      class="tools"
    >
      <NInput
        v-model:value="code"
        size="small"
        :placeholder="t('reservations.allocation.scan')"
        class="scan"
        @keydown.enter.prevent="code && allocate({ code })"
      >
        <template #prefix><ScanLine :size="14" /></template>
      </NInput>
      <NPopselect
        :options="assetOptions"
        trigger="click"
        scrollable
        :on-update:value="(id: Id) => allocate({ asset: id })"
        @update:show="(open: boolean) => open && loadCandidates()"
      >
        <NButton size="small" :loading="busy">{{
          t('reservations.allocation.candidates')
        }}</NButton>
        <template #empty
          ><span class="muted">{{ t('reservations.allocation.noCandidates') }}</span></template
        >
      </NPopselect>
      <template v-for="consumable in candidates?.consumables ?? []" :key="consumable.id">
        <div class="row consumable">
          <span class="small"
            >{{ consumable.model.full_name }} · {{ consumable.location.name }} ({{
              consumable.available_quantity
            }})</span
          >
          <NInputNumber
            v-model:value="consumableQuantity"
            size="small"
            :min="1"
            :max="Math.min(consumable.available_quantity, item.quantity_missing)"
            style="width: 90px"
          />
          <NButton
            size="small"
            @click="allocate({ consumable: consumable.id, quantity: consumableQuantity })"
            >{{ t('reservations.actions.allocate') }}</NButton
          >
        </div>
      </template>
    </div>
  </div>
</template>

<style scoped>
.pick {
  width: 280px;
}
.item {
  display: grid;
  gap: 8px;
  padding: 12px 0;
  border-bottom: 1px solid var(--ar-border);
}
.item:last-child {
  border-bottom: none;
}
.head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}
.free-tag {
  margin-left: 6px;
  padding: 0 5px;
  border: 1px solid var(--ar-warning);
  border-radius: 2px;
  color: var(--ar-warning);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.counts {
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
}
.done {
  color: var(--ar-success);
}
.reduced {
  margin-left: 4px;
  color: var(--ar-warning);
  font-size: 12px;
}
.small {
  font-size: 11.5px;
}
.availability {
  font-weight: 500;
  text-align: right;
}
.enough {
  color: var(--ar-success);
}
.short {
  color: var(--ar-warning);
}
.allocations {
  margin: 0;
  padding: 0;
  list-style: none;
}
.allocations li {
  display: grid;
  grid-template-columns: 110px 1fr auto auto auto;
  align-items: center;
  gap: 10px;
  padding: 4px 8px;
  border-left: 2px solid var(--ar-primary);
  background: var(--ar-surface-sunken);
  margin-bottom: 3px;
}
.note {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--ar-warning);
  font-size: 11.5px;
}
.state {
  min-width: 28px;
  text-align: right;
}
.tools {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
}
.scan {
  max-width: 300px;
}
.scan :deep(input) {
  font-family: var(--ar-font-mono);
}
.consumable {
  width: 100%;
}
</style>
