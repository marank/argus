<script setup lang="ts">
import { MessageSquarePlus, Minus, PackageSearch, Plus, Send, Trash2 } from '@lucide/vue'
import {
  NButton,
  NForm,
  NFormItem,
  NInput,
  NInputNumber,
  NRadioButton,
  NRadioGroup,
} from 'naive-ui'
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import DateField from '@/components/common/DateField.vue'
import { toIsoDate } from '@/composables/useFormat'
import type { Id } from '@/types/common'
import type { Duration, ReservationInput } from '@/types/reservations'

import type { CartLine } from './types'

/** The request being assembled: selected devices, then purpose and period. */
const props = defineProps<{
  busy: boolean
  canChooseRequester: boolean
  requesterPlaceholder?: string
}>()
const lines = defineModel<CartLine[]>('lines', { required: true })
const emit = defineEmits<{ submit: [data: ReservationInput] }>()
const { t } = useI18n()

const today = new Date().setHours(0, 0, 0, 0)
const form = reactive({
  title: '',
  notes: '',
  duration: 'temporary' as Duration,
  range: [today, today + 4 * 86400000] as [number, number],
  start: today,
  requester: null as Id | null,
})
const openNote = ref<string | null>(null)

const total = computed(() => lines.value.reduce((sum, line) => sum + line.quantity, 0))
const canSubmit = computed(() => form.title.trim() && lines.value.length > 0)

function submit() {
  const temporary = form.duration === 'temporary'
  emit('submit', {
    title: form.title,
    notes: form.notes,
    duration: form.duration,
    start_date: toIsoDate(temporary ? form.range[0] : form.start)!,
    end_date: temporary ? toIsoDate(form.range[1]) : null,
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
      <span v-if="total" class="mono badge">{{ total }}</span>
    </header>

    <div v-if="!lines.length" class="empty">
      <PackageSearch :size="30" :stroke-width="1.3" />
      <p>{{ t('reservations.new.cartEmpty') }}</p>
    </div>

    <template v-else>
      <ul class="lines">
        <li v-for="(line, index) in lines" :key="line.key">
          <div class="line">
            <div class="text">
              <strong>{{ line.label }}</strong>
              <small v-if="line.description" class="custom-hint">
                <MessageSquarePlus :size="12" /> {{ t('reservations.new.customHint') }}
              </small>
              <button
                type="button"
                class="note-link"
                @click="openNote = openNote === line.key ? null : line.key"
              >
                {{ line.note || t('reservations.new.addNote') }}
              </button>
            </div>
            <NInputNumber
              v-model:value="line.quantity"
              :min="1"
              :max="500"
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
      </ul>

      <NForm
        class="details ar-form"
        label-placement="top"
        size="small"
        :show-feedback="false"
        @submit.prevent="submit"
      >
        <div class="eyebrow">{{ t('reservations.new.details') }}</div>
        <NFormItem>
          <template #label><FieldLabel :label="t('reservations.purpose')" required /></template>
          <NInput v-model:value="form.title" :placeholder="t('reservations.purposePlaceholder')" />
        </NFormItem>
        <NFormItem>
          <template #label>
            <FieldLabel
              :label="t('reservations.duration')"
              :help="t('reservations.new.durationHelp')"
            />
          </template>
          <NRadioGroup v-model:value="form.duration" class="duration">
            <NRadioButton value="temporary">{{ t('enums.duration.temporary') }}</NRadioButton>
            <NRadioButton value="permanent">{{ t('enums.duration.permanent') }}</NRadioButton>
          </NRadioGroup>
        </NFormItem>
        <NFormItem v-if="form.duration === 'temporary'" :label="t('reservations.period')">
          <DateField
            v-model:value="form.range"
            type="daterange"
            :is-date-disabled="(ts: number) => ts < today"
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem v-else :label="t('reservations.startDate')">
          <DateField
            v-model:value="form.start"
            type="date"
            :is-date-disabled="(ts: number) => ts < today"
            style="width: 100%"
          />
        </NFormItem>
        <NFormItem v-if="props.canChooseRequester" :label="t('reservations.requestedFor')">
          <EntitySelect
            v-model="form.requester"
            :fetcher="usersApi.list"
            :label="(u) => u.display_name"
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
.cart {
  position: sticky;
  top: 16px;
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
  min-width: 22px;
  padding: 0 6px;
  border-radius: 10px;
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
.warn {
  color: var(--ar-warning);
}
.details {
  padding-top: 4px;
}
.details .eyebrow {
  margin-bottom: 10px;
}
.duration {
  display: flex;
  width: 100%;
}
.duration :deep(.n-radio-button) {
  flex: 1;
  text-align: center;
}
</style>
