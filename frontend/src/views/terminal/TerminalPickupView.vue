<script setup lang="ts">
import type { Id } from '@/types/common'
import {
  CalendarClock,
  Check,
  CircleCheckBig,
  Info,
  MessageSquareWarning,
  Search,
  UserRound,
  Users,
  X,
} from '@lucide/vue'
import { onClickOutside, useDebounceFn, useIdle } from '@vueuse/core'
import { NButton, NInput, NSelect, NSkeleton } from 'naive-ui'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { terminalApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import SignaturePad from '@/components/terminal/SignaturePad.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import { categoryIcon } from '@/utils/icons'
import { allocationCode, allocationModel } from '@/utils/requests'

/**
 * Pickup at the shared terminal in three steps:
 * check the devices (with optional notes), confirm who collects, sign.
 */
const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const router = useRouter()
const { weekday } = useFormat()
const { busy, run } = useAction()
const confirmDialog = useConfirm()

type Step = 'devices' | 'person' | 'sign' | 'done'

const assetRequest = ref<Schemas['TerminalPickupDetailOut'] | null>(null)
const step = ref<Step>('devices')
const notes = reactive<Record<Id, string>>({})
const openNote = ref<Id | null>(null)
const generalNote = ref('')
const noteInput = ref<InstanceType<typeof NInput> | null>(null)

async function toggleNote(id: Id) {
  openNote.value = openNote.value === id ? null : id
  await nextTick()
  if (openNote.value !== null) noteInput.value?.focus()
}

const collector = ref<'requester' | 'other'>('requester')
const personQuery = ref('')
const people = ref<Schemas['TerminalPersonOut'][]>([])
/** Picked from the search; without a pick the typed name is recorded as is. */
const person = ref<Schemas['TerminalPersonOut'] | null>(null)

const pad = ref<InstanceType<typeof SignaturePad>>()
const signed = ref(false)

/** IT member named on the record: who prepared the pickup, unless changed here. */
const handedOutBy = ref<Id | null>(null)
const staff = ref<Schemas['TerminalStaffOut'][]>([])
const changingStaff = ref(false)
const staffOptions = computed(() =>
  staff.value.map((s) => ({ value: s.id, label: s.display_name })),
)
const handedOutByName = computed(() => {
  const chosen = staff.value.find((s) => s.id === handedOutBy.value)
  const preparer = assetRequest.value?.prepared_by ?? assetRequest.value?.handled_by
  return chosen?.display_name ?? preparer?.display_name ?? '—'
})

async function changeStaff() {
  if (!staff.value.length) staff.value = await terminalApi.staff()
  changingStaff.value = true
}

onMounted(async () => {
  try {
    assetRequest.value = await terminalApi.get(props.id)
    handedOutBy.value =
      assetRequest.value.prepared_by?.id ?? assetRequest.value.handled_by?.id ?? null
    // IT can skip the check, e.g. for sealed devices: start with who collects.
    if (assetRequest.value.skip_device_check) step.value = 'person'
  } catch {
    void router.replace({ name: 'terminal' })
  }
})

const devices = computed(() =>
  (assetRequest.value?.items ?? []).flatMap((item) =>
    // License seats are already assigned; only things to take along are checked here.
    item.allocations.filter((a) => !a.license).map((allocation) => ({ item, allocation })),
  ),
)

const collectorName = computed(() => {
  if (collector.value === 'requester') return assetRequest.value?.requester.display_name ?? ''
  return person.value?.display_name ?? personQuery.value.trim()
})

const searchPeople = useDebounceFn(async (q: string) => {
  people.value = q.trim().length >= 2 ? await terminalApi.people(q) : []
}, 200)
watch(personQuery, (q) => {
  if (person.value && q !== person.value.display_name) person.value = null
  void searchPeople(q)
})

function pick(p: Schemas['TerminalPersonOut']) {
  person.value = p
  personQuery.value = p.display_name
  people.value = []
}

// Matches open as a dropdown under the field; tapping elsewhere keeps the typed name.
const personBox = ref<HTMLElement | null>(null)
const dropdownOpen = ref(false)
watch(personQuery, () => (dropdownOpen.value = true))
onClickOutside(personBox, () => (dropdownOpen.value = false))

function deviceLabel(allocation: Schemas['TerminalAllocationOut']) {
  return allocationModel(allocation)
}

async function confirm() {
  if (!assetRequest.value || !pad.value || pad.value.isEmpty()) return
  const done = await run(() =>
    terminalApi.sign(assetRequest.value!.id, {
      handed_out_by: handedOutBy.value,
      received_by:
        collector.value === 'requester'
          ? assetRequest.value!.requester.id
          : (person.value?.id ?? null),
      received_by_name: collectorName.value,
      signature: pad.value!.toDataUrl(),
      notes: generalNote.value,
      allocation_notes: Object.entries(notes)
        .filter(([, note]) => note.trim())
        .map(([allocation, note]) => ({ allocation, note })),
    }),
  )
  if (done) {
    step.value = 'done'
    setTimeout(() => router.push({ name: 'terminal' }), 8000)
  }
}

// An abandoned pickup returns to the overview so the next person starts clean.
const { idle } = useIdle(120_000)
const stopIdle = watch(
  idle,
  (isIdle) => isIdle && step.value !== 'done' && router.push({ name: 'terminal' }),
)
onBeforeUnmount(stopIdle)

const STEPS = computed<Step[]>(() =>
  assetRequest.value?.skip_device_check ? ['person', 'sign'] : ['devices', 'person', 'sign'],
)

async function cancelPickup() {
  const leave = await confirmDialog(t('terminal.cancelPickup'), {
    positiveText: t('terminal.cancelConfirm'),
    negativeText: t('terminal.cancelKeep'),
  })
  if (leave) void router.push({ name: 'terminal' })
}
</script>

<template>
  <NSkeleton v-if="!assetRequest" height="300px" />

  <div v-else-if="step === 'done'" class="done">
    <CircleCheckBig :size="88" :stroke-width="1.3" />
    <h1>{{ t('terminal.doneTitle') }}</h1>
    <p>{{ t('terminal.doneText', { name: collectorName }) }}</p>
    <NButton size="large" type="primary" @click="router.push({ name: 'terminal' })">
      {{ t('terminal.finish') }}
    </NButton>
  </div>

  <div v-else class="pickup">
    <div class="head">
      <div class="title">
        <span class="eyebrow">{{ assetRequest.number }}</span>
        <h1>{{ assetRequest.requester.display_name }}</h1>
        <span class="muted">{{ assetRequest.title }}</span>
      </div>
      <ol class="steps">
        <li
          v-for="(s, index) in STEPS"
          :key="s"
          :class="{ active: step === s, past: STEPS.indexOf(step) > index }"
        >
          <span class="num mono">{{ index + 1 }}</span>{{ t(`terminal.steps.${s}`) }}
        </li>
      </ol>
      <!-- Leaves the pickup without saving anything; back to the list of pickups. -->
      <NButton size="large" secondary class="cancel" @click="cancelPickup">
        <template #icon><X :size="20" /></template>
        {{ t('common.cancel') }}
      </NButton>
    </div>

    <!-- 1 · Devices -->
    <section v-if="step === 'devices'" class="panel">
      <div class="panel-head">
        <div>
          <h2>{{ t('terminal.devicesTitle') }}</h2>
          <p class="muted">{{ t('terminal.devicesHint') }}</p>
        </div>
        <div class="facts">
          <span class="fact">{{ t('terminal.deviceCount', devices.length) }}</span>
          <span class="fact">
            <CalendarClock :size="16" />
            <template v-if="assetRequest.end_date">
              {{ t('terminal.returnBy', { date: weekday(assetRequest.end_date) }) }}
            </template>
            <template v-else>{{ t('terminal.keep') }}</template>
          </span>
        </div>
      </div>
      <ul class="devices">
        <li
          v-for="{ allocation } in devices"
          :key="allocation.id"
          :class="{ noted: notes[allocation.id]?.trim() }"
        >
          <span class="device-icon">
            <component
              :is="categoryIcon(allocation.category_icon)"
              :size="26"
              :stroke-width="1.5"
            />
          </span>
          <strong class="device-name">{{ deviceLabel(allocation) }}</strong>
          <template v-if="allocation.asset">
            <span class="code">
              <small>{{ t('inventory.fields.inventoryNumber') }}</small>
              <span class="mono">{{ allocation.asset.inventory_number }}</span>
            </span>
            <span class="code">
              <small>{{ t('inventory.fields.serialNumber') }}</small>
              <span class="mono">{{ allocation.asset.serial_number || '–' }}</span>
            </span>
          </template>
          <span v-else class="code wide">
            <small>{{ t('common.quantity') }}</small>
            <span class="mono">{{ allocation.quantity }}×</span>
          </span>
          <NButton
            size="large"
            :type="notes[allocation.id]?.trim() ? 'warning' : 'default'"
            secondary
            class="note-button"
            @click="toggleNote(allocation.id)"
          >
            <template #icon><MessageSquareWarning :size="20" /></template>
            {{ notes[allocation.id]?.trim() ? t('terminal.noteAdded') : t('terminal.addNote') }}
          </NButton>
          <p v-if="allocation.handout_note" class="it-note">
            <Info :size="15" /> {{ t('terminal.itNote', { note: allocation.handout_note }) }}
          </p>
          <NInput
            v-if="openNote === allocation.id"
            :ref="(el) => el && (noteInput = el as InstanceType<typeof NInput>)"
            v-model:value="notes[allocation.id]"
            class="note-input"
            type="textarea"
            size="large"
            :autosize="{ minRows: 2 }"
            :placeholder="t('handover.deviceNotePlaceholder')"
          />
          <p v-else-if="notes[allocation.id]?.trim()" class="own-note">
            {{ notes[allocation.id] }}
          </p>
        </li>
      </ul>
      <NInput
        v-model:value="generalNote"
        type="textarea"
        size="large"
        :autosize="{ minRows: 2 }"
        :placeholder="t('terminal.generalNote')"
      />
      <div class="actions">
        <NButton size="large" type="primary" class="next" @click="step = 'person'">
          {{ t('terminal.devicesOk') }}
        </NButton>
      </div>
    </section>

    <!-- 2 · Who collects -->
    <section v-else-if="step === 'person'" class="panel">
      <h2>{{ t('terminal.personTitle') }}</h2>
      <div class="choices">
        <button
          type="button"
          class="choice"
          :class="{ active: collector === 'requester' }"
          @click="collector = 'requester'"
        >
          <UserRound :size="30" :stroke-width="1.5" />
          <span>
            <strong>{{ t('terminal.iAm', { name: assetRequest.requester.display_name }) }}</strong>
            <small class="muted">{{ assetRequest.department?.name }}</small>
          </span>
        </button>
        <button
          type="button"
          class="choice"
          :class="{ active: collector === 'other' }"
          @click="collector = 'other'"
        >
          <Users :size="30" :stroke-width="1.5" />
          <span>
            <strong>{{ t('terminal.someoneElse') }}</strong>
            <small class="muted">{{
              t('terminal.someoneElseHint', { name: assetRequest.requester.display_name })
            }}</small>
          </span>
        </button>
      </div>
      <div v-if="collector === 'other'" ref="personBox" class="other">
        <NInput
          v-model:value="personQuery"
          class="touch-input"
          clearable
          :placeholder="t('terminal.searchPerson')"
          @focus="dropdownOpen = true"
          @keydown.escape="dropdownOpen = false"
        >
          <template #prefix><Search :size="22" /></template>
          <template v-if="person" #suffix><Check :size="22" class="picked" /></template>
        </NInput>
        <div v-if="dropdownOpen && people.length && !person" class="people" role="listbox">
          <button
            v-for="p in people"
            :key="p.id"
            type="button"
            role="option"
            :aria-selected="false"
            class="person"
            @click="pick(p)"
          >
            <UserRound :size="22" :stroke-width="1.5" />
            <span class="person-name">
              <strong>{{ p.display_name }}</strong>
              <span v-if="p.employee_number" class="mono muted">{{ p.employee_number }}</span>
            </span>
            <span class="muted">{{ p.department?.name }}</span>
          </button>
        </div>
      </div>
      <div class="actions">
        <NButton
          v-if="!assetRequest.skip_device_check"
          size="large"
          class="back"
          @click="step = 'devices'"
        >
          {{ t('common.back') }}
        </NButton>
        <NButton
          size="large"
          type="primary"
          class="next"
          :disabled="!collectorName"
          @click="step = 'sign'"
        >
          {{ t('terminal.continue') }}
        </NButton>
      </div>
    </section>

    <!-- 3 · Signature -->
    <section v-else class="panel">
      <h2>{{ t('terminal.signTitle') }}</h2>
      <div class="sign-layout">
        <!-- What is being signed for. -->
        <aside class="receipt">
          <div class="receipt-facts">
            <div>
              <span class="eyebrow">{{ t('handover.receivedBy') }}</span>
              <strong>{{ collectorName }}</strong>
              <small v-if="collector === 'other'" class="muted">
                {{ t('terminal.someoneElseHint', { name: assetRequest.requester.display_name }) }}
              </small>
            </div>
            <div>
              <span class="eyebrow">{{ t('requests.endDate') }}</span>
              <strong v-if="assetRequest.end_date" class="mono">{{
                weekday(assetRequest.end_date)
              }}</strong>
              <strong v-else>{{ t('terminal.keep') }}</strong>
            </div>
            <div class="handed-out-by">
              <span class="eyebrow">{{ t('handover.handedOutBy') }}</span>
              <NSelect
                v-if="changingStaff"
                v-model:value="handedOutBy"
                size="large"
                :options="staffOptions"
                filterable
              />
              <template v-else>
                <strong>{{ handedOutByName }}</strong>
                <button type="button" class="link" @click="changeStaff">
                  {{ t('terminal.changeStaff') }}
                </button>
              </template>
            </div>
          </div>
          <div class="eyebrow">{{ t('terminal.deviceCount', devices.length) }}</div>
          <ul class="compact">
            <li v-for="{ allocation } in devices" :key="allocation.id">
              <component
                :is="categoryIcon(allocation.category_icon)"
                :size="20"
                :stroke-width="1.5"
                class="compact-icon"
              />
              <span class="compact-text">
                <span>{{ deviceLabel(allocation) }}</span>
                <span class="mono muted">{{ allocationCode(allocation) }}</span>
                <span v-if="notes[allocation.id]?.trim()" class="note">{{
                  notes[allocation.id]
                }}</span>
              </span>
            </li>
          </ul>
          <p v-if="generalNote.trim()" class="general-note">{{ generalNote }}</p>
        </aside>
        <div class="signature">
          <SignaturePad ref="pad" :height="340" @change="(empty: boolean) => (signed = !empty)" />
          <p class="legal">
            {{ t('terminal.legal', { name: assetRequest.requester.display_name }) }}
          </p>
        </div>
      </div>
      <div class="actions">
        <NButton size="large" class="back" @click="step = 'person'">{{ t('common.back') }}</NButton>
        <NButton
          size="large"
          type="primary"
          class="next"
          :disabled="!signed"
          :loading="busy"
          @click="confirm"
        >
          <template #icon><Check :size="20" /></template>
          {{ t('terminal.confirm') }}
        </NButton>
      </div>
    </section>
  </div>
</template>

<style scoped>
.handed-out-by {
  grid-column: 1 / -1;
}
.link {
  justify-self: start;
  padding: 0;
  border: none;
  background: none;
  color: var(--ar-primary);
  font: inherit;
  font-size: 13px;
  cursor: pointer;
}
.pickup {
  display: grid;
  gap: 20px;
}
.head {
  display: grid;
  grid-template-columns: 1fr auto auto;
  gap: 20px;
  align-items: center;
}
.title {
  display: grid;
  gap: 2px;
}
h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.02em;
}
h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
}
.steps {
  display: flex;
  gap: 18px;
  margin: 0;
  padding: 0;
  list-style: none;
  color: var(--ar-text-subtle);
  font-size: 15px;
}
.steps li {
  display: flex;
  align-items: center;
  gap: 8px;
}
.steps .num {
  display: grid;
  place-items: center;
  width: 26px;
  height: 26px;
  border: 1px solid currentColor;
  border-radius: 50%;
  font-size: 12px;
}
.steps .active {
  color: var(--ar-primary);
  font-weight: 600;
}
.steps .past {
  color: var(--ar-success);
}
.panel {
  display: grid;
  gap: 16px;
  padding: 24px;
  border: 1px solid var(--ar-border);
  border-radius: 4px;
  background: var(--ar-surface);
}
.panel > p {
  margin: -8px 0 0;
}
.devices,
.compact {
  display: grid;
  gap: 10px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.panel-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px 24px;
}
.panel-head p {
  margin: 4px 0 0;
}
.facts {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.fact {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid var(--ar-border);
  border-radius: 999px;
  background: var(--ar-surface-sunken);
  font-size: 15px;
  white-space: nowrap;
}
/* One row per device: icon, name, codes in fixed columns, note button. */
.devices li {
  display: grid;
  grid-template-columns: 52px minmax(0, 1fr) 150px 190px 196px;
  align-items: center;
  gap: 6px 18px;
  padding: 14px 16px;
  border: 1px solid var(--ar-border);
  border-radius: 4px;
}
.devices li.noted {
  border-color: color-mix(in srgb, var(--ar-warning) 55%, transparent);
}
.device-icon {
  display: grid;
  place-items: center;
  width: 52px;
  height: 52px;
  border-radius: 4px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
.device-name {
  font-size: 19px;
  overflow-wrap: anywhere;
}
.code {
  display: grid;
  gap: 2px;
}
.code.wide {
  grid-column: span 2;
}
.code small {
  color: var(--ar-text-subtle);
  font-size: 12px;
}
.code .mono {
  font-size: 15px;
}
.it-note,
.own-note,
.note-input {
  grid-column: 2 / -1;
  margin: 0;
}
.it-note {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ar-text-muted);
  font-size: 14px;
}
.note-button {
  width: 100%;
}
.own-note {
  color: var(--ar-warning);
  font-size: 15px;
}
.choices {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.choice {
  display: flex;
  gap: 16px;
  align-items: center;
  min-height: 110px;
  padding: 18px 20px;
  border: 2px solid var(--ar-border);
  border-radius: 6px;
  background: var(--ar-surface);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.choice span {
  display: grid;
  gap: 4px;
}
.choice strong {
  font-size: 19px;
}
.choice.active {
  border-color: var(--ar-primary);
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
.other {
  position: relative;
}
/* Dropdown under the field, above the buttons below it. */
.people {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  left: 0;
  z-index: 10;
  display: grid;
  max-height: 360px;
  overflow-y: auto;
  border: 1px solid var(--ar-border-strong);
  border-radius: 4px;
  background: var(--ar-surface);
  box-shadow: 0 12px 32px rgb(0 0 0 / 0.35);
}
/* Large enough for a finger: the terminal is a touch screen. */
.touch-input {
  --n-height: 60px !important;
  --n-font-size: 19px !important;
  --n-padding-left: 16px !important;
  --n-padding-right: 16px !important;
}
.touch-input :deep(.n-input__prefix) {
  margin-right: 10px;
}
.picked {
  color: var(--ar-success);
}
.person {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 14px;
  min-height: 60px;
  padding: 12px 18px;
  text-align: left;
  border: 0;
  border-bottom: 1px solid var(--ar-border);
  background: none;
  color: inherit;
  font: inherit;
  font-size: 17px;
  cursor: pointer;
}
.person-name {
  display: flex;
  align-items: baseline;
  gap: 12px;
}
.person-name .mono {
  font-size: 14px;
}
.person:last-child {
  border-bottom: 0;
}
.person:hover,
.person:active {
  background: var(--ar-primary-soft);
}
/* Receipt on the left, a large signature field on the right. */
.sign-layout {
  display: grid;
  grid-template-columns: minmax(260px, 340px) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}
.receipt {
  display: grid;
  gap: 14px;
  padding: 18px;
  border-radius: 4px;
  background: var(--ar-surface-sunken);
}
.receipt-facts {
  display: grid;
  gap: 14px;
  padding-bottom: 14px;
  border-bottom: 1px solid var(--ar-border);
}
.receipt-facts div {
  display: grid;
  gap: 3px;
}
.receipt-facts strong {
  font-size: 19px;
}
.compact li {
  display: grid;
  grid-template-columns: 22px minmax(0, 1fr);
  gap: 12px;
  align-items: start;
}
.compact-icon {
  margin-top: 2px;
  color: var(--ar-primary);
}
.compact-text {
  display: grid;
  gap: 1px;
  font-size: 16px;
}
.compact-text .mono {
  font-size: 13px;
}
.note,
.general-note {
  color: var(--ar-warning);
  font-size: 14px;
}
.general-note {
  margin: 0;
  padding-top: 12px;
  border-top: 1px solid var(--ar-border);
}
.signature {
  display: grid;
  gap: 10px;
}
.legal {
  margin: 0;
  color: var(--ar-text-muted);
  font-size: 14px;
}
.actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
.next {
  min-width: 220px;
}
/* Going back sits on the left, away from the step's main action. */
.back {
  margin-right: auto;
}
.done {
  display: grid;
  justify-items: center;
  gap: 16px;
  padding: 60px 0;
  text-align: center;
  color: var(--ar-success);
}
.done h1 {
  color: var(--ar-text);
}
.done p {
  margin: 0;
  font-size: 18px;
  color: var(--ar-text-muted);
}
@media (max-width: 900px) {
  .head {
    grid-template-columns: 1fr auto;
  }
  .steps {
    grid-column: 1 / -1;
    grid-row: 2;
  }
  .choices,
  .sign-layout {
    grid-template-columns: 1fr;
  }
  .devices li {
    grid-template-columns: 52px minmax(0, 1fr) auto;
  }
  .device-name {
    grid-column: 2 / -1;
  }
  .code.wide {
    grid-column: auto;
  }
  .note-button {
    grid-column: 2 / -1;
    justify-self: start;
    width: auto;
  }
}
</style>
