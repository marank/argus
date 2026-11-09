<script setup lang="ts">
import { NButton, NFormItem, NModal } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import DateField from '@/components/common/DateField.vue'
import { useAction } from '@/composables/useAction'
import { fromIsoDate, toIsoDate, useFormat } from '@/composables/useFormat'

/** Move the return date of handed-out devices. */
const props = defineProps<{ assetRequest: Pick<Schemas['AssetRequestOut'], 'id' | 'end_date'> }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()
const { weekday } = useFormat()
const { busy, run } = useAction()

const WEEKS = [1, 2, 4]

const today = () => fromIsoDate(toIsoDate(Date.now()))!
const current = computed(() => fromIsoDate(props.assetRequest.end_date) ?? 0)
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
  const saved = await run(() => requestsApi.extend(props.assetRequest.id, toIsoDate(end.value)!))
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
    :title="t('requests.actions.extend')"
    style="max-width: 440px"
  >
    <p class="muted">
      {{ t('requests.extend.current', { date: weekday(assetRequest.end_date) }) }}
    </p>
    <NFormItem :label="t('requests.extend.newDate')" :show-feedback="false">
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
            {{ t('requests.extend.weeks', { count: weeks }, weeks) }}
          </NButton>
        </div>
      </div>
    </NFormItem>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :disabled="!end" :loading="busy" @click="save">{{
          t('requests.actions.extend')
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
