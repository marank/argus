<script setup lang="ts">
import { NButton, NFormItem, NModal } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { reservationsApi } from '@/api/reservations'
import DateField from '@/components/common/DateField.vue'
import { useAction } from '@/composables/useAction'
import { fromIsoDate, toIsoDate, useFormat } from '@/composables/useFormat'
import type { Reservation } from '@/types/reservations'

/** Move the return date of handed-out devices. */
const props = defineProps<{ reservation: Pick<Reservation, 'id' | 'end_date'> }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [reservation: Reservation] }>()
const { t } = useI18n()
const { weekday } = useFormat()
const { busy, run } = useAction()

const WEEKS = [1, 2, 4]

const today = () => fromIsoDate(toIsoDate(Date.now()))!
const current = computed(() => fromIsoDate(props.reservation.end_date) ?? 0)
/** Extensions count from the current return date, or from today once it has passed. */
const base = computed(() => Math.max(current.value, today()))
/** Calendar days, not 24h steps, so daylight saving time does not shift the date. */
const plusDays = (ts: number, days: number) => {
  const date = new Date(ts)
  date.setDate(date.getDate() + days)
  return date.getTime()
}

const end = ref<number | null>(null)
// Immediate: the dashboard mounts the dialog already open.
watch(
  show,
  (visible) => {
    if (visible) end.value = plusDays(base.value, 7)
  },
  { immediate: true },
)

const disabled = (ts: number) => ts <= current.value || ts < today()

async function save() {
  const saved = await run(
    () => reservationsApi.extend(props.reservation.id, toIsoDate(end.value)!),
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
    :title="t('reservations.actions.extend')"
    style="max-width: 440px"
  >
    <p class="muted">
      {{ t('reservations.extend.current', { date: weekday(reservation.end_date) }) }}
    </p>
    <NFormItem :label="t('reservations.extend.newDate')" :show-feedback="false">
      <div class="when">
        <DateField v-model:value="end" :is-date-disabled="disabled" style="width: 100%" />
        <div class="row">
          <NButton
            v-for="weeks in WEEKS"
            :key="weeks"
            size="small"
            secondary
            @click="end = plusDays(base, weeks * 7)"
          >
            {{ t('reservations.extend.weeks', { count: weeks }, weeks) }}
          </NButton>
        </div>
      </div>
    </NFormItem>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :disabled="!end" :loading="busy" @click="save">{{
          t('reservations.actions.extend')
        }}</NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.when {
  display: grid;
  gap: 8px;
  width: 100%;
}
</style>
