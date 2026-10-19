<script setup lang="ts">
import { NButton, NFormItem, NModal, NSwitch } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { locationsApi } from '@/api/masterdata'
import { reservationsApi } from '@/api/reservations'
import DateField from '@/components/common/DateField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import type { Id } from '@/types/common'
import type { HandoverMode, Reservation } from '@/types/reservations'

import HandoverModeSelect from './HandoverModeSelect.vue'

const props = defineProps<{ reservation: Reservation }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [reservation: Reservation] }>()
const { t } = useI18n()
const { weekday } = useFormat()
const { busy, run } = useAction()

const mode = ref<HandoverMode>('pickup')
const skipCheck = ref(false)
const when = ref<number | null>(null)
const where = ref<Id | null>(null)
watch(show, (visible) => {
  if (!visible) return
  const r = props.reservation
  mode.value = r.handover_mode
  skipCheck.value = r.skip_device_check
  // The date set when approving; the employee is told this one with the ready message.
  when.value = r.pickup_at ? new Date(r.pickup_at).getTime() : null
  where.value = r.pickup_location?.id ?? null
})

async function save() {
  const saved = await run(
    () =>
      reservationsApi.markReady(props.reservation.id, {
        handover_mode: mode.value,
        skip_device_check: mode.value === 'pickup' && skipCheck.value,
        pickup_at: when.value ? new Date(when.value).toISOString() : null,
        pickup_location: where.value,
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
    :title="t('reservations.actions.markReady')"
    style="max-width: 720px"
  >
    <p class="muted">{{ t('handover.readyHint') }}</p>
    <HandoverModeSelect v-model="mode" />
    <div class="cols">
      <NFormItem
        :label="mode === 'delivery' ? t('handover.deliveryAt') : t('reservations.pickupAt')"
        :show-feedback="false"
      >
        <div class="when">
          <DateField
            v-model:value="when"
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
      <NFormItem
        v-if="mode !== 'delivery'"
        :label="t('reservations.pickupLocation')"
        :show-feedback="false"
      >
        <EntitySelect
          v-model="where"
          :fetcher="locationsApi.list"
          :params="{ is_pickup_point: true }"
          :label="(l) => l.full_name"
          :initial="reservation.pickup_location as never"
        />
      </NFormItem>
    </div>
    <label v-if="mode === 'pickup'" class="skip">
      <span>
        <span>{{ t('handover.skipCheck') }}</span>
        <small class="muted">{{ t('handover.skipCheckHint') }}</small>
      </span>
      <NSwitch v-model:value="skipCheck" />
    </label>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" @click="save">{{
          t('reservations.actions.markReady')
        }}</NButton>
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
.cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-top: 14px;
}
.skip {
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
.skip > span {
  display: grid;
  gap: 2px;
}
</style>
