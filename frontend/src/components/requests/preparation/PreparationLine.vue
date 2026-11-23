<script setup lang="ts">
import type { Id } from '@/types/common'
import { Check, ChevronDown, CircleCheck, Lock, Sparkles, X } from '@lucide/vue'
import { NButton, NDropdown, NSelect, useMessage } from 'naive-ui'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import StatusTag from '@/components/common/StatusTag.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { showError } from '@/composables/useErrorPopover'
import { categoryIcon } from '@/utils/icons'
import { isReturnable, itemLabel } from '@/utils/requests'

import ResolveFreeText from '../ResolveFreeText.vue'

/**
 * One line of a request: a row per unit, all built alike (category icon, what it is,
 * one round button on the right). Allocated devices and seats can be removed with ✕,
 * open units show a dashed frame; consumables are ticked off as set aside as a whole.
 */
const props = defineProps<{
  assetRequest: Schemas['AssetRequestOut']
  item: Schemas['AssetRequestItemOut']
  editable: boolean
  /** Devices or seats the pool holds for the line; without any there is nothing to fill automatically. */
  pool?: number
  /** An allocation just added by the scan field, shown highlighted. */
  highlight?: Id | null
  /** Pool counts for the request's period, shown before IT confirms. */
  availability?: Schemas['CountsOut'] | null
}>()
const emit = defineEmits<{ updated: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()
const { dateTime } = useFormat()
const { busy, run } = useAction()
const message = useMessage()

const target = computed(() => props.item.quantity_confirmed ?? props.item.quantity_requested)
const complete = computed(() => !props.item.is_free_text && props.item.quantity_missing === 0)
const consumable = computed(
  () =>
    props.item.asset_model?.tracking === 'bulk' || props.item.allocations.some((a) => a.consumable),
)
const icon = computed(() => categoryIcon(props.item.category_icon))
/** "Laptops · " before the model of every row. */
const prefix = computed(() => (props.item.category_name ? `${props.item.category_name} · ` : ''))
const open = computed(() =>
  props.item.is_free_text
    ? Math.max(target.value - props.item.quantity_allocated, 0)
    : props.item.quantity_missing,
)
/** Before the hand-out, devices can still be put back; ready requests go back to preparation. */
const removable = (a: Schemas['AllocationOut']) =>
  !a.handed_out_at && (props.editable || props.assetRequest.status === 'ready')

const canAuto = computed(
  () =>
    props.editable &&
    props.assetRequest.status === 'confirmed' &&
    !complete.value &&
    !props.item.is_free_text &&
    !consumable.value &&
    (props.pool ?? 0) > 0,
)

/** Finished lines fold to their header while preparing, so the open ones stand out. */
const expanded = ref(false)
/** A complete line folds its devices away; a click or Enter/Space on the header opens it. */
const foldable = computed(() => props.editable && complete.value)
const toggle = () => {
  if (foldable.value) expanded.value = !expanded.value
}
const folded = computed(
  () =>
    props.editable &&
    complete.value &&
    !expanded.value &&
    !props.item.allocations.some((a) => a.id === props.highlight),
)

async function autoAllocate() {
  const result = await run(() => requestsApi.autoAllocate(props.assetRequest.id, props.item.id))
  if (!result) return
  message.info(t('requests.actions.autoAllocated', { count: result.allocated }, result.allocated))
  emit('updated', result.asset_request)
}

async function remove(allocationId: Id) {
  const updated = await run(() => requestsApi.removeAllocation(props.assetRequest.id, allocationId))
  if (updated) emit('updated', updated)
}

// --- Consumables: ticked off as set aside -----------------------------------------------

const stockChoices = ref<{ key: Id; label: string }[] | null>(null)
const tick = ref<HTMLElement | null>(null)

async function toggleConsumable() {
  if (complete.value) {
    let updated: Schemas['AssetRequestOut'] | undefined
    for (const allocation of props.item.allocations.filter(removable)) {
      updated = await run(() => requestsApi.removeAllocation(props.assetRequest.id, allocation.id))
      if (!updated) break
    }
    if (updated) emit('updated', updated)
    return
  }
  const missing = props.item.quantity_missing
  const candidates = await run(() => requestsApi.candidates(props.item.id))
  if (!candidates) return
  const enough = candidates.consumables.filter((c) => c.available_quantity >= missing)
  if (!enough.length) {
    showError(t('requests.preparation.notEnough', { count: missing }), tick.value)
  } else if (enough.length === 1) {
    await takeConsumable(enough[0]!.id)
  } else {
    stockChoices.value = enough.map((c) => ({
      key: c.id,
      label: `${c.location.name} (${c.available_quantity})`,
    }))
  }
}

async function takeConsumable(consumableId: Id) {
  stockChoices.value = null
  const updated = await run(() =>
    requestsApi.allocate(props.assetRequest.id, {
      item: props.item.id,
      consumable: consumableId,
      quantity: props.item.quantity_missing,
    }),
  )
  if (updated) emit('updated', updated)
}

const consumableModel = computed(
  () =>
    props.item.asset_model?.full_name ??
    props.item.allocations.find((a) => a.consumable)?.consumable?.model.full_name ??
    itemLabel(props.item),
)
const consumableFrom = computed(() =>
  [...new Set(props.item.allocations.map((a) => a.consumable?.location.name).filter(Boolean))].join(
    ', ',
  ),
)
const consumed = computed(() => props.item.allocations.some((a) => a.handed_out_at))

// --- License seats: the first open row picks one ------------------------------------------

const candidates = ref<Schemas['CandidatesOut'] | null>(null)
const licenseId = ref<Id | null>(null)
const licenseOptions = computed(() =>
  (candidates.value?.licenses ?? []).map((l) => ({
    value: l.id,
    label: `${l.model.full_name}${l.reference ? ` (${l.reference})` : ''} · ${t('requests.allocation.freeSeats', { count: l.free_seats })}`,
  })),
)
const chosenLicense = computed(() =>
  candidates.value?.licenses.find((l) => l.id === licenseId.value),
)
const deviceOptions = computed(() =>
  (candidates.value?.devices ?? []).map((d) => ({
    value: d.id,
    label: `${d.inventory_number} · ${d.model.full_name}`,
  })),
)

async function loadLicenses() {
  candidates.value ??= (await run(() => requestsApi.candidates(props.item.id))) ?? null
}

async function chooseLicense(id: Id) {
  licenseId.value = id
  // Seats for a person are assigned at once; device licenses ask for the device first.
  if (chosenLicense.value?.assign_to === 'user') await assignSeat({ license: id })
}

async function assignSeat(data: Partial<Omit<Schemas['AllocateIn'], 'item'>>) {
  const updated = await run(() =>
    requestsApi.allocate(props.assetRequest.id, { item: props.item.id, quantity: 1, ...data }),
  )
  licenseId.value = null
  candidates.value = null
  if (updated) emit('updated', updated)
}
</script>

<template>
  <section class="line">
    <!-- eslint-disable-next-line vuejs-accessibility/no-static-element-interactions -- a button (role, tabindex, Enter/Space) while the line can fold, plain text otherwise -->
    <header
      class="head"
      :class="{ foldable }"
      :role="foldable ? 'button' : undefined"
      :tabindex="foldable ? 0 : undefined"
      :aria-expanded="foldable ? expanded : undefined"
      @click="toggle"
      @keydown.enter.space.prevent="toggle"
    >
      <strong>{{ itemLabel(item) }}</strong>
      <span v-if="item.is_free_text" class="free-tag">{{ t('requests.freeText') }}</span>
      <span class="count mono">
        {{ consumable ? (complete ? target : 0) : item.quantity_allocated }} / {{ target }}
        <span
          v-if="
            item.quantity_confirmed !== null && item.quantity_confirmed < item.quantity_requested
          "
          class="reduced"
          :title="t('requests.quantities.requested')"
          >({{ item.quantity_requested }})</span
        >
      </span>
      <CircleCheck v-if="complete" :size="15" class="done" />
      <span
        v-if="availability"
        class="availability"
        :class="availability.available >= target ? 'enough' : 'short'"
        :title="
          availability.reserved
            ? t('requests.allocation.periodReserved', { count: availability.reserved })
            : undefined
        "
        >{{ t('requests.allocation.periodFree', { count: availability.available }) }}</span
      >
      <span class="spacer" />
      <NButton v-if="canAuto" size="tiny" secondary :loading="busy" @click.stop="autoAllocate">
        <template #icon><Sparkles :size="13" /></template>
        {{ t('requests.preparation.auto') }}
      </NButton>
      <ChevronDown
        v-if="editable && complete"
        :size="15"
        class="muted fold"
        :class="{ up: !folded }"
      />
    </header>

    <ResolveFreeText
      v-if="item.is_free_text && ['submitted', 'confirmed'].includes(assetRequest.status)"
      :asset-request="assetRequest"
      :item="item"
      @updated="(r) => emit('updated', r)"
    />

    <template v-if="!folded">
      <!-- Consumables: one row, ticked off once the whole quantity is set aside. -->
      <div v-if="consumable" class="row" :class="{ open: !complete }">
        <component :is="icon" :size="16" class="icon" />
        <span class="text">
          {{ prefix }}{{ target }}× {{ consumableModel }}
          <span v-if="consumableFrom" class="muted">
            · {{ t('requests.allocation.consumableFrom', { location: consumableFrom }) }}</span
          >
        </span>
        <span v-if="consumed" class="muted small">{{ t('requests.allocation.consumed') }}</span>
        <NDropdown
          v-else
          :show="!!stockChoices"
          :options="stockChoices ?? []"
          trigger="manual"
          placement="bottom-end"
          @select="takeConsumable"
          @clickoutside="stockChoices = null"
        >
          <span ref="tick">
            <NButton
              circle
              size="tiny"
              :type="complete ? 'success' : 'default'"
              :dashed="!complete"
              :disabled="!editable && !(complete && assetRequest.status === 'ready')"
              :loading="busy"
              :title="complete ? t('requests.preparation.untick') : t('requests.preparation.tick')"
              @click="toggleConsumable"
            >
              <template #icon><Check :size="13" /></template>
            </NButton>
          </span>
        </NDropdown>
      </div>

      <template v-else>
        <div
          v-for="allocation in item.allocations"
          :key="allocation.id"
          class="row"
          :class="{ added: allocation.id === highlight }"
        >
          <component :is="icon" :size="16" class="icon" />
          <span v-if="allocation.asset" class="text">
            {{ prefix }}{{ allocation.asset.model.full_name }} ·
            <RouterLink :to="{ name: 'asset', params: { id: allocation.asset.id } }" class="mono">{{
              allocation.asset.inventory_number
            }}</RouterLink>
            <span v-if="allocation.asset.serial_number" class="mono muted">
              · {{ allocation.asset.serial_number }}</span
            >
          </span>
          <span v-else-if="allocation.license" class="text">
            {{ prefix }}{{ allocation.license.model.full_name }} ·
            <RouterLink :to="{ name: 'license', params: { id: allocation.license.id } }">{{
              allocation.license.device
                ? allocation.license.device.inventory_number
                : t('requests.preparation.seatFor', { name: assetRequest.requester.display_name })
            }}</RouterLink>
          </span>
          <span v-if="allocation.handout_note" class="note" :title="allocation.handout_note">{{
            allocation.handout_note
          }}</span>
          <span
            v-if="allocation.allocated_by"
            class="muted small by"
            :title="
              t('requests.allocation.allocatedBy', {
                name: allocation.allocated_by.display_name,
                date: dateTime(allocation.allocated_at),
              })
            "
            >{{ allocation.allocated_by.display_name }}</span
          >
          <StatusTag
            v-if="allocation.returned_at"
            group="assetStatus"
            :value="allocation.returned_damaged ? 'in_repair' : 'in_stock'"
          />
          <span v-else-if="allocation.handed_out_at" class="muted small">{{
            isReturnable(allocation)
              ? t('requests.allocation.handedOut')
              : t('requests.allocation.consumed')
          }}</span>
          <NButton
            v-else-if="removable(allocation)"
            circle
            size="tiny"
            secondary
            :title="t('common.remove')"
            @click="remove(allocation.id)"
          >
            <template #icon><X :size="13" /></template>
          </NButton>
        </div>

        <div
          v-for="n in open"
          :key="`open-${n}`"
          class="row open"
          :class="{ locked: item.is_free_text }"
        >
          <component :is="icon" :size="16" class="icon" />
          <!-- The first open seat of a software line is where a license is picked. -->
          <template v-if="item.is_software && editable && n === 1">
            <NSelect
              :value="licenseId"
              size="small"
              :options="licenseOptions"
              :placeholder="t('requests.allocation.chooseLicense')"
              :loading="busy"
              class="pick"
              @focus="loadLicenses"
              @update:value="chooseLicense"
            />
            <NSelect
              v-if="chosenLicense?.assign_to === 'device'"
              size="small"
              :options="deviceOptions"
              :placeholder="t('requests.allocation.chooseDevice')"
              class="pick"
              @update:value="(asset: Id) => assignSeat({ license: licenseId!, asset })"
            />
            <span v-if="candidates && !licenseOptions.length" class="muted small">
              {{ t('requests.allocation.noSeats') }}
              <RouterLink :to="{ name: 'licenses' }">{{
                t('requests.allocation.toLicenses')
              }}</RouterLink>
            </span>
          </template>
          <span v-else class="text">
            {{ itemLabel(item) }} ·
            {{
              item.is_free_text
                ? t('requests.preparation.needsModel')
                : t('requests.preparation.open')
            }}
          </span>
          <Lock v-if="item.is_free_text" :size="14" class="muted" />
        </div>
      </template>
    </template>
  </section>
</template>

<style scoped>
.line {
  display: grid;
  gap: 6px;
  padding: 12px 0;
  border-bottom: 1px solid var(--ar-border);
}
.line:last-child {
  border-bottom: none;
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 24px;
}
.foldable {
  cursor: pointer;
}
.spacer {
  flex: 1;
}
.count {
  color: var(--ar-text-subtle);
  font-size: 12px;
}
.reduced {
  margin-left: 2px;
  color: var(--ar-warning);
}
.done {
  color: var(--ar-success);
}
.fold {
  transition: transform 0.15s;
}
.fold.up {
  transform: rotate(180deg);
}
.free-tag {
  padding: 0 5px;
  border: 1px solid var(--ar-warning);
  border-radius: 2px;
  color: var(--ar-warning);
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.availability {
  font-size: 11.5px;
}
.availability.enough {
  color: var(--ar-success);
}
.availability.short {
  color: var(--ar-warning);
}
.row {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 26px;
  padding: 5px 8px 5px 10px;
  border: 1px solid var(--ar-border-strong);
  border-radius: 6px;
  transition:
    background 0.6s,
    border-color 0.6s;
}
.row.open {
  border-style: dashed;
  color: var(--ar-text-subtle);
}
.row.locked {
  border-color: var(--ar-border);
  background: var(--ar-surface-sunken);
}
.row.added {
  border-color: var(--ar-success);
  background: color-mix(in srgb, var(--ar-success) 12%, transparent);
}
.icon {
  flex: none;
  color: var(--ar-text-subtle);
}
.text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.mono {
  font-family: var(--ar-font-mono);
  font-size: 12px;
}
.small {
  font-size: 11.5px;
}
.by {
  flex: none;
  white-space: nowrap;
}
.note {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: var(--ar-warning);
  font-size: 11.5px;
}
.pick {
  flex: 1;
  min-width: 0;
  max-width: 320px;
}
</style>
