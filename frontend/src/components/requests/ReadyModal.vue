<script setup lang="ts">
import { NButton, NFormItem, NModal, NSwitch } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { locationsApi } from '@/api/masterdata'
import { requestsApi } from '@/api/requests'
import DateField from '@/components/common/DateField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import type { Id } from '@/types/common'
import type { HandoverMode, AssetRequest } from '@/types/requests'

import HandoverModeSelect from './HandoverModeSelect.vue'

const props = defineProps<{ assetRequest: AssetRequest }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [assetRequest: AssetRequest] }>()
const { t } = useI18n()
const { weekday } = useFormat()
const { busy, run } = useAction()

const mode = ref<HandoverMode>('pickup')
const skipCheck = ref(false)
const notify = ref(true)
const when = ref<number | null>(null)
const where = ref<Id | null>(null)
watch(show, (visible) => {
  if (!visible) return
  const r = props.assetRequest
  mode.value = r.handover_mode
  skipCheck.value = r.skip_device_check
  // A direct hand-out is usually done with the employee there: no message by default.
  notify.value = r.origin !== 'direct'
  // The date set when confirming; the employee is told this one with the ready message.
  when.value = r.pickup_at ? new Date(r.pickup_at).getTime() : null
  where.value = r.pickup_location?.id ?? null
})

async function save() {
  const saved = await run(
    () =>
      requestsApi.markReady(props.assetRequest.id, {
        handover_mode: mode.value,
        skip_device_check: mode.value === 'pickup' && skipCheck.value,
        pickup_at: when.value ? new Date(when.value).toISOString() : null,
        pickup_location: where.value,
        notify: notify.value,
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
    :title="t('requests.actions.markReady')"
    style="max-width: 720px"
  >
    <p class="muted">{{ t('handover.readyHint') }}</p>
    <HandoverModeSelect v-model="mode" />
    <div class="cols">
      <NFormItem
        :label="mode === 'delivery' ? t('handover.deliveryAt') : t('requests.pickupAt')"
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
          <small v-if="assetRequest.requested_pickup_date" class="muted wish">{{
            t('requests.wishHint', { date: weekday(assetRequest.requested_pickup_date) })
          }}</small>
        </div>
      </NFormItem>
      <NFormItem
        v-if="mode !== 'delivery'"
        :label="t('requests.pickupLocation')"
        :show-feedback="false"
      >
        <EntitySelect
          v-model="where"
          :fetcher="locationsApi.list"
          :params="{ is_pickup_point: true }"
          :label="(l) => l.full_name"
          :initial="assetRequest.pickup_location as never"
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
    <label class="skip">
      <span>
        <span>{{ t('handover.notify') }}</span>
        <small class="muted">{{ t('handover.notifyHint') }}</small>
      </span>
      <NSwitch v-model:value="notify" />
    </label>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" @click="save">{{
          t('requests.actions.markReady')
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
  align-items: start;
  margin-top: 18px;
}
/* The pickup wish below the date must not push the location down. */
.cols :deep(.n-form-item-blank) {
  align-items: flex-start;
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
