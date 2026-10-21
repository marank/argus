<script setup lang="ts">
import type { Id } from '@/types/common'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NModal, NTable } from 'naive-ui'
import { reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { locationsApi } from '@/api/masterdata'
import { reservationsApi } from '@/api/reservations'
import EntitySelect from '@/components/common/EntitySelect.vue'
import DateField from '@/components/common/DateField.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import type { HandoverMode, Reservation } from '@/types/reservations'
import { itemLabel } from '@/utils/reservations'

import HandoverModeSelect from './HandoverModeSelect.vue'

/** Confirm a request (possibly with reduced quantities) or just change the pickup. */
const props = defineProps<{ reservation: Reservation; mode: 'confirm' | 'schedule' }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [reservation: Reservation] }>()
const { t } = useI18n()
const { weekday } = useFormat()
const { busy, run } = useAction()

const form = reactive({
  quantities: {} as Record<Id, number>,
  pickup_at: null as number | null,
  pickup_location: null as Id | null,
  comment: '',
  handover_mode: 'pickup' as HandoverMode,
})

function defaultPickup(): number {
  const day = props.reservation.requested_pickup_date ?? props.reservation.start_date
  const start = new Date(`${day}T09:00:00`)
  return Math.max(start.getTime(), Date.now())
}

watch(show, (visible) => {
  if (!visible) return
  const r = props.reservation
  form.quantities = Object.fromEntries(
    r.items.map((i) => [i.id, i.quantity_confirmed ?? i.quantity_requested]),
  )
  form.pickup_at = r.pickup_at ? new Date(r.pickup_at).getTime() : defaultPickup()
  form.pickup_location = r.pickup_location?.id ?? null
  form.comment = r.it_comment
  form.handover_mode = r.handover_mode
})

async function save() {
  const pickup_at = form.pickup_at ? new Date(form.pickup_at).toISOString() : null
  const saved = await run(
    () =>
      props.mode === 'confirm'
        ? reservationsApi.confirm(props.reservation.id, {
            items: Object.entries(form.quantities).map(([id, quantity]) => ({
              id,
              quantity_confirmed: quantity,
            })),
            pickup_at,
            pickup_location: form.pickup_location,
            comment: form.comment,
          })
        : reservationsApi.schedule(props.reservation.id, {
            pickup_at,
            pickup_location: form.pickup_location,
            handover_mode: form.handover_mode,
          }),
    t('common.saved'),
  )
  if (saved) {
    show.value = false
    emit('saved', saved)
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="
      mode === 'confirm'
        ? t('reservations.actions.confirmTitle')
        : t('reservations.actions.schedule')
    "
    style="max-width: 720px"
  >
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <template v-if="mode === 'confirm'">
        <p class="muted">{{ t('reservations.actions.confirmHint') }}</p>
        <NTable size="small" :bordered="false" class="items">
          <thead>
            <tr>
              <th>{{ t('reservations.items') }}</th>
              <th class="num">{{ t('reservations.quantities.requested') }}</th>
              <th class="num">{{ t('reservations.quantities.confirmed') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in reservation.items" :key="item.id">
              <td>
                {{ itemLabel(item) }}
                <div v-if="item.note" class="muted small">{{ item.note }}</div>
              </td>
              <td class="num mono">{{ item.quantity_requested }}</td>
              <td class="num">
                <NInputNumber
                  v-model:value="form.quantities[item.id]"
                  class="qty"
                  :min="0"
                  :max="item.quantity_requested"
                  size="small"
                  style="width: 100px"
                />
              </td>
            </tr>
          </tbody>
        </NTable>
      </template>
      <div class="cols">
        <NFormItem :label="t('reservations.pickupAt')">
          <div class="when">
            <DateField
              v-model:value="form.pickup_at"
              type="datetime"
              :minutes="[0, 15, 30, 45]"
              clearable
              style="width: 100%"
            />
            <small v-if="reservation.requested_pickup_date" class="muted wish">{{
              t('reservations.wishHint', { date: weekday(reservation.requested_pickup_date) })
            }}</small>
          </div>
        </NFormItem>
        <NFormItem :label="t('reservations.pickupLocation')">
          <EntitySelect
            v-model="form.pickup_location"
            :fetcher="locationsApi.list"
            :params="{ is_pickup_point: true }"
            :label="(l) => l.full_name"
            :initial="reservation.pickup_location as never"
          />
        </NFormItem>
      </div>
      <NFormItem v-if="mode === 'schedule'" :label="t('handover.method')">
        <HandoverModeSelect v-model="form.handover_mode" style="width: 100%" />
      </NFormItem>
      <NFormItem v-if="mode === 'confirm'" :label="t('reservations.itComment')">
        <NInput
          v-model:value="form.comment"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 5 }"
        />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" @click="save">
          {{ mode === 'confirm' ? t('reservations.actions.confirm') : t('common.save') }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.when {
  display: grid;
  gap: 4px;
  width: 100%;
}
.items {
  margin-bottom: 14px;
}
.num {
  text-align: right;
}
/* Quantity inputs line up with the numbers in the "requested" column. */
.qty {
  margin-left: auto;
}
.qty :deep(input) {
  text-align: right;
  font-family: var(--ar-font-mono);
}
.small {
  font-size: 11.5px;
}
.cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}
</style>
