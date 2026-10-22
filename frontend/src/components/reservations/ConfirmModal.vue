<script setup lang="ts">
import type { Id } from '@/types/common'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NModal, NSwitch, NTable } from 'naive-ui'
import { computed, reactive, watch } from 'vue'
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

/**
 * `confirm`: tell the employee the request is fine, possibly with fewer devices; editing a
 * confirmed request keeps what is already allocated. `schedule`: change how, when and where
 * the devices reach the employee once it is ready.
 */
const props = defineProps<{ reservation: Reservation; mode: 'confirm' | 'schedule' }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [reservation: Reservation] }>()
const { t } = useI18n()
const { weekday } = useFormat()
const { busy, run } = useAction()
/** Changing the quantities of a request that is already confirmed. */
const editing = computed(() => props.reservation.status === 'confirmed')

const form = reactive({
  quantities: {} as Record<Id, number>,
  pickup_at: null as number | null,
  pickup_location: null as Id | null,
  comment: '',
  handover_mode: 'pickup' as HandoverMode,
  notify: true,
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
  // As when marking it ready: a direct hand-out is usually done with the employee there.
  form.notify = r.origin !== 'direct'
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
            comment: form.comment,
          })
        : reservationsApi.schedule(props.reservation.id, {
            pickup_at,
            pickup_location: form.pickup_location,
            handover_mode: form.handover_mode,
            notify: form.notify,
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
      mode === 'schedule'
        ? t('reservations.actions.schedule')
        : editing
          ? t('reservations.confirming.editTitle')
          : t('reservations.actions.confirmTitle')
    "
    style="max-width: 720px"
  >
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <template v-if="mode === 'confirm'">
        <p class="muted">
          {{
            editing ? t('reservations.confirming.editHint') : t('reservations.actions.confirmHint')
          }}
        </p>
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
                <div v-if="item.quantity_allocated" class="muted small">
                  {{ t('reservations.confirming.allocated', { count: item.quantity_allocated }) }}
                </div>
              </td>
              <td class="num mono">{{ item.quantity_requested }}</td>
              <td class="num">
                <NInputNumber
                  v-model:value="form.quantities[item.id]"
                  class="qty"
                  :min="item.quantity_allocated"
                  :max="item.quantity_requested"
                  size="small"
                  style="width: 100px"
                />
              </td>
            </tr>
          </tbody>
        </NTable>
        <NFormItem :label="t('reservations.itComment')">
          <NInput
            v-model:value="form.comment"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 5 }"
          />
        </NFormItem>
      </template>
      <div v-else class="cols">
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
      <template v-if="mode === 'schedule'">
        <NFormItem :label="t('handover.method')">
          <HandoverModeSelect v-model="form.handover_mode" style="width: 100%" />
        </NFormItem>
        <label class="notify">
          <span>
            <span>{{ t('handover.notify') }}</span>
            <small class="muted">{{ t('handover.notifyChangeHint') }}</small>
          </span>
          <NSwitch v-model:value="form.notify" />
        </label>
      </template>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" @click="save">
          {{
            mode === 'confirm' && !editing ? t('reservations.actions.confirm') : t('common.save')
          }}
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
.notify {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 14px;
  padding: 10px 12px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  cursor: pointer;
}
.notify > span {
  display: grid;
  gap: 2px;
}
.cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
  align-items: start;
}
/* The pickup wish below the date must not push the location down. */
.cols :deep(.n-form-item-blank) {
  align-items: flex-start;
}
</style>
