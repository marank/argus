<script setup lang="ts">
import { MessageSquarePlus, Minus, PackageSearch, Plus, Send, Trash2 } from '@lucide/vue'
import { NButton, NForm, NFormItem, NInput, NInputNumber } from 'naive-ui'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { toIsoDate } from '@/composables/useFormat'
import type { UserRef } from '@/types/accounts'
import type { Id } from '@/types/common'
import type { ReservationInput } from '@/types/reservations'

import { periodQuery, type CartLine, type RequestPeriod } from './types'

/**
 * The request being assembled: selected devices, then purpose; the period comes from the card above.
 * For a direct hand-out (`direct`) the lines are specific devices and stocks.
 */
const props = defineProps<{
  period: RequestPeriod
  busy: boolean
  canChooseRequester: boolean
  requesterPlaceholder?: string
  direct?: boolean
  /** Prefilled details, e.g. when asking again for an earlier request. */
  initial?: { title: string; notes: string; requester: UserRef | null } | null
}>()
const lines = defineModel<CartLine[]>('lines', { required: true })
const emit = defineEmits<{ submit: [data: ReservationInput] }>()
const { t } = useI18n()

const form = reactive({
  title: '',
  notes: '',
  requester: null as Id | null,
})
watch(
  () => props.initial,
  (initial) => {
    if (initial)
      Object.assign(form, {
        title: initial.title,
        notes: initial.notes,
        requester: initial.requester?.id ?? null,
      })
  },
  { immediate: true },
)
const openNote = ref<string | null>(null)

const total = computed(() => lines.value.reduce((sum, line) => sum + line.quantity, 0))
const canSubmit = computed(() => form.title.trim() && lines.value.length > 0)

function submit() {
  const { end } = periodQuery(props.period)
  const first = props.period.duration === 'permanent' ? props.period.start : props.period.range[0]
  emit('submit', {
    title: form.title,
    notes: form.notes,
    duration: props.period.duration,
    start_date: toIsoDate(first)!,
    end_date: end ?? null,
    requested_pickup_date: toIsoDate(props.period.pickup),
    requester: form.requester,
    items: lines.value.map(({ category, asset_model, description, quantity, note }) => ({
      category: category ?? null,
      asset_model: asset_model ?? null,
      description: description ?? '',
      quantity,
      note,
    })),
  })
}
</script>

<template>
  <aside class="cart">
    <header>
      <h2>{{ t('reservations.new.cart') }}</h2>
      <span v-if="total" :key="total" class="mono badge">{{ total }}</span>
    </header>

    <div v-if="!lines.length" class="empty">
      <PackageSearch :size="30" :stroke-width="1.3" />
      <p>{{ direct ? t('reservations.direct.cartEmpty') : t('reservations.new.cartEmpty') }}</p>
    </div>

    <template v-else>
      <TransitionGroup tag="ul" name="cart-line" class="lines">
        <li v-for="(line, index) in lines" :key="line.key">
          <div class="line">
            <div class="text">
              <span v-if="line.code" class="mono code">{{ line.code }}</span>
              <strong>{{ line.label }}</strong>
              <small v-if="line.description" class="custom-hint">
                <MessageSquarePlus :size="12" /> {{ t('reservations.new.customHint') }}
              </small>
              <button
                v-if="!direct"
                type="button"
                class="note-link"
                @click="openNote = openNote === line.key ? null : line.key"
              >
                {{ line.note || t('reservations.new.addNote') }}
              </button>
            </div>
            <NInputNumber
              v-if="!line.asset"
              v-model:value="line.quantity"
              :min="1"
              :max="line.max ?? 500"
              size="small"
              button-placement="both"
              class="qty"
            >
              <template #minus-icon><Minus :size="12" /></template>
              <template #add-icon><Plus :size="12" /></template>
            </NInputNumber>
            <NButton
              quaternary
              circle
              size="tiny"
              :title="t('common.remove')"
              @click="lines.splice(index, 1)"
            >
              <template #icon><Trash2 :size="14" /></template>
            </NButton>
          </div>
          <NInput
            v-if="openNote === line.key"
            v-model:value="line.note"
            size="small"
            :placeholder="t('reservations.new.itemNote')"
          />
          <small v-if="line.available !== null && line.quantity > line.available" class="warn">
            {{ t('reservations.new.available', { count: line.available }) }}
          </small>
        </li>
      </TransitionGroup>

      <NForm
        class="details ar-form"
        label-placement="top"
        size="medium"
        :show-feedback="false"
        @submit.prevent="submit"
      >
        <div class="eyebrow">{{ t('reservations.new.details') }}</div>
        <NFormItem>
          <template #label><FieldLabel :label="t('reservations.purpose')" required /></template>
          <NInput v-model:value="form.title" :placeholder="t('reservations.purposePlaceholder')" />
        </NFormItem>
        <NFormItem v-if="props.canChooseRequester" :label="t('reservations.requestedFor')">
          <EntitySelect
            v-model="form.requester"
            :fetcher="usersApi.list"
            :label="(u) => u.display_name"
            :initial="(initial?.requester ?? null) as never"
            :placeholder="requesterPlaceholder"
          />
        </NFormItem>
        <NFormItem :label="t('reservations.notes')">
          <NInput
            v-model:value="form.notes"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 5 }"
          />
        </NFormItem>
        <NButton type="primary" block attr-type="submit" :disabled="!canSubmit" :loading="busy">
          <template #icon><Send :size="15" /></template>
          {{ t('reservations.new.submit') }}
        </NButton>
      </NForm>
    </template>
  </aside>
</template>

<style scoped>
/* New lines slide in, removed ones fade out. */
.cart-line-enter-active,
.cart-line-leave-active {
  transition:
    opacity 0.2s ease,
    transform 0.2s ease;
}
.cart-line-enter-from,
.cart-line-leave-to {
  opacity: 0;
  transform: translateX(8px);
}
.cart-line-move {
  transition: transform 0.2s ease;
}
.cart {
  display: grid;
  gap: 14px;
  padding: 16px 18px 18px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
.badge {
  /* Centered digits; re-keyed on change so the count pops. */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 6px;
  border-radius: 10px;
  line-height: 1;
  animation: ar-pop 0.25s ease-out;
  background: var(--ar-primary);
  color: var(--ar-on-primary);
  font-size: 11px;
  font-weight: 700;
  text-align: center;
}
.empty {
  display: grid;
  justify-items: center;
  gap: 8px;
  padding: 24px 8px;
  color: var(--ar-text-subtle);
  text-align: center;
}
.empty p {
  margin: 0;
  color: var(--ar-text-muted);
}
.lines {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}
.lines li {
  display: grid;
  gap: 6px;
  padding: 10px 0;
  border-bottom: 1px solid var(--ar-border);
}
.lines li:first-child {
  padding-top: 0;
}
.line {
  display: flex;
  align-items: flex-start;
  gap: 8px;
}
.text {
  display: grid;
  flex: 1;
  min-width: 0;
}
.text strong {
  overflow-wrap: anywhere;
}
.custom-hint {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--ar-text-muted);
  font-size: 11.5px;
}
.note-link {
  padding: 0;
  border: 0;
  background: none;
  color: var(--ar-text-subtle);
  font: inherit;
  font-size: 11.5px;
  text-align: left;
  cursor: pointer;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.note-link:hover {
  color: var(--ar-primary);
}
.qty {
  width: 104px;
}
.qty :deep(input) {
  text-align: center;
}
.warn {
  color: var(--ar-warning);
}
.details {
  padding-top: 4px;
}
.details .eyebrow {
  margin-bottom: 10px;
}
.code {
  color: var(--ar-primary);
  font-size: 11.5px;
}
</style>
