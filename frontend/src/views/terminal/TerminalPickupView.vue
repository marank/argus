<script setup lang="ts">
import type { Id } from '@/types/common'
import {
  ArrowLeft,
  Check,
  CircleCheckBig,
  MessageSquareWarning,
  RotateCcw,
  UserRound,
  Users,
} from '@lucide/vue'
import { useDebounceFn, useIdle } from '@vueuse/core'
import { NButton, NInput, NSkeleton } from 'naive-ui'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { terminalApi } from '@/api/reservations'
import SignaturePad from '@/components/terminal/SignaturePad.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import type { Allocation, Reservation, TerminalPerson } from '@/types/reservations'
import { itemLabel } from '@/utils/reservations'

/**
 * Pickup at the shared terminal in three steps:
 * check the devices (with optional notes), confirm who collects, sign.
 */
const props = defineProps<{ id: Id }>()
const { t } = useI18n()
const router = useRouter()
const { weekday } = useFormat()
const { busy, run } = useAction()

type Step = 'devices' | 'person' | 'sign' | 'done'

const reservation = ref<Reservation | null>(null)
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
const people = ref<TerminalPerson[]>([])
const person = ref<TerminalPerson | null>(null)
const freeName = ref('')

const pad = ref<InstanceType<typeof SignaturePad> | null>(null)
const signed = ref(false)

onMounted(async () => {
  try {
    reservation.value = await terminalApi.get(props.id)
  } catch {
    router.replace({ name: 'terminal' })
  }
})

const devices = computed(() =>
  (reservation.value?.items ?? []).flatMap((item) =>
    item.allocations.map((allocation) => ({ item, allocation })),
  ),
)

const collectorName = computed(() => {
  if (collector.value === 'requester') return reservation.value?.requester.display_name ?? ''
  return person.value?.display_name ?? freeName.value.trim()
})

const searchPeople = useDebounceFn(async (q: string) => {
  people.value = q.trim().length >= 2 ? await terminalApi.people(q) : []
}, 200)
watch(personQuery, searchPeople)

function deviceLabel(allocation: Allocation) {
  return allocation.asset?.model.full_name ?? allocation.consumable?.model.full_name ?? ''
}

async function confirm() {
  if (!reservation.value || !pad.value || pad.value.isEmpty()) return
  const done = await run(() =>
    terminalApi.sign(reservation.value!.id, {
      received_by:
        collector.value === 'requester'
          ? reservation.value!.requester.id
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

const STEPS: Step[] = ['devices', 'person', 'sign']
</script>

<template>
  <NSkeleton v-if="!reservation" height="300px" />

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
      <NButton size="large" quaternary @click="router.push({ name: 'terminal' })">
        <template #icon><ArrowLeft :size="22" /></template>
        {{ t('common.back') }}
      </NButton>
      <div class="title">
        <span class="eyebrow">{{ reservation.number }}</span>
        <h1>{{ reservation.requester.display_name }}</h1>
        <span class="muted">{{ reservation.title }}</span>
      </div>
      <ol class="steps">
        <li
          v-for="(s, index) in STEPS"
          :key="s"
          :class="{ active: step === s, past: STEPS.indexOf(step) > index }"
        >
          <span class="num mono">{{ index + 1 }}</span
          >{{ t(`terminal.steps.${s}`) }}
        </li>
      </ol>
    </div>

    <!-- 1 · Devices -->
    <section v-if="step === 'devices'" class="panel">
      <h2>{{ t('terminal.devicesTitle') }}</h2>
      <p class="muted">{{ t('terminal.devicesHint') }}</p>
      <ul class="devices">
        <li v-for="{ item, allocation } in devices" :key="allocation.id">
          <div class="device">
            <div>
              <strong>{{ deviceLabel(allocation) }}</strong>
              <div class="mono muted">
                <template v-if="allocation.asset">
                  {{ allocation.asset.inventory_number }} · {{ allocation.asset.serial_number }}
                </template>
                <template v-else>{{ allocation.quantity }}× · {{ itemLabel(item) }}</template>
              </div>
            </div>
            <NButton
              size="large"
              :type="notes[allocation.id] ? 'warning' : 'default'"
              secondary
              @click="toggleNote(allocation.id)"
            >
              <template #icon><MessageSquareWarning :size="20" /></template>
              {{ notes[allocation.id] ? t('terminal.noteAdded') : t('terminal.addNote') }}
            </NButton>
          </div>
          <NInput
            v-if="openNote === allocation.id"
            :ref="(el) => el && (noteInput = el as InstanceType<typeof NInput>)"
            v-model:value="notes[allocation.id]"
            type="textarea"
            size="large"
            :autosize="{ minRows: 2 }"
            :placeholder="t('handover.deviceNotePlaceholder')"
          />
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
            <strong>{{ t('terminal.iAm', { name: reservation.requester.display_name }) }}</strong>
            <small class="muted">{{ reservation.department?.name }}</small>
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
              t('terminal.someoneElseHint', { name: reservation.requester.display_name })
            }}</small>
          </span>
        </button>
      </div>
      <div v-if="collector === 'other'" class="other">
        <NInput
          v-model:value="personQuery"
          size="large"
          clearable
          :placeholder="t('terminal.searchPerson')"
          @update:value="person = null"
        />
        <div v-if="people.length && !person" class="people">
          <button
            v-for="p in people"
            :key="p.id"
            type="button"
            class="person"
            @click="((person = p), (personQuery = p.display_name))"
          >
            <strong>{{ p.display_name }}</strong>
            <span class="muted">{{ p.department?.name }}</span>
          </button>
        </div>
        <NInput
          v-if="!person"
          v-model:value="freeName"
          size="large"
          :placeholder="t('terminal.freeName')"
        />
      </div>
      <div class="actions">
        <NButton size="large" @click="step = 'devices'">{{ t('common.back') }}</NButton>
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
      <div class="summary">
        <div>
          <span class="eyebrow">{{ t('handover.receivedBy') }}</span>
          <strong>{{ collectorName }}</strong>
        </div>
        <div>
          <span class="eyebrow">{{ t('reservations.items') }}</span>
          <strong>{{ devices.length }}</strong>
        </div>
        <div v-if="reservation.end_date">
          <span class="eyebrow">{{ t('reservations.endDate') }}</span>
          <strong class="mono">{{ weekday(reservation.end_date) }}</strong>
        </div>
      </div>
      <ul class="compact">
        <li v-for="{ allocation } in devices" :key="allocation.id">
          <span class="mono">{{
            allocation.asset?.inventory_number ?? `${allocation.quantity}×`
          }}</span>
          <span>{{ deviceLabel(allocation) }}</span>
          <span v-if="notes[allocation.id]" class="note">{{ notes[allocation.id] }}</span>
        </li>
      </ul>
      <p class="legal">{{ t('terminal.legal', { name: reservation.requester.display_name }) }}</p>
      <SignaturePad ref="pad" @change="(empty: boolean) => (signed = !empty)" />
      <div class="actions">
        <NButton size="large" @click="step = 'person'">{{ t('common.back') }}</NButton>
        <NButton size="large" quaternary @click="pad?.clear()">
          <template #icon><RotateCcw :size="18" /></template>
          {{ t('terminal.clear') }}
        </NButton>
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
.pickup {
  display: grid;
  gap: 20px;
}
.head {
  display: grid;
  grid-template-columns: auto 1fr auto;
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
.devices li {
  display: grid;
  gap: 10px;
  padding: 14px 16px;
  border: 1px solid var(--ar-border);
  border-radius: 4px;
}
.device {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  font-size: 18px;
}
.device .mono {
  font-size: 14px;
  margin-top: 2px;
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
  display: grid;
  gap: 10px;
}
.people {
  display: grid;
  gap: 6px;
}
.person {
  display: flex;
  justify-content: space-between;
  padding: 14px 16px;
  border: 1px solid var(--ar-border);
  border-radius: 4px;
  background: var(--ar-surface-sunken);
  color: inherit;
  font: inherit;
  font-size: 17px;
  cursor: pointer;
}
.summary {
  display: flex;
  flex-wrap: wrap;
  gap: 16px 40px;
}
.summary div {
  display: grid;
  gap: 4px;
}
.summary strong {
  font-size: 20px;
}
.compact li {
  display: grid;
  grid-template-columns: 120px 1fr auto;
  gap: 14px;
  padding: 6px 10px;
  border-left: 3px solid var(--ar-primary);
  background: var(--ar-surface-sunken);
}
.note {
  color: var(--ar-warning);
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
    grid-template-columns: auto 1fr;
  }
  .steps {
    grid-column: 1 / -1;
  }
  .choices {
    grid-template-columns: 1fr;
  }
}
</style>
