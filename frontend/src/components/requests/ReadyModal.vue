<script setup lang="ts">
import { NButton, NFormItem, NModal, NSwitch } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { locationsApi } from '@/api/masterdata'
import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import DateTimeField from '@/components/common/DateTimeField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import type { Id } from '@/types/common'
import { nextFullHour } from '@/utils/requests'

import HandoverModeSelect from './HandoverModeSelect.vue'
import { onlyPickupPoint } from './pickupPoint'

const props = defineProps<{ assetRequest: Schemas['AssetRequestOut'] }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()
const { weekday } = useFormat()
const { busy, run } = useAction()

const mode = ref<Schemas['HandoverMode']>('pickup')
const skipCheck = ref(false)
const notify = ref(true)
const when = ref<number | null>(null)
const where = ref<Id | null>(null)
/** The location shown before the list has loaded: the planned one or the only one there is. */
const whereInitial = ref<Schemas['LocationOut'] | null>(null)
watch(show, async (visible) => {
  if (!visible) return
  const r = props.assetRequest
  mode.value = r.handover_mode
  skipCheck.value = r.skip_device_check
  // A direct hand-out is usually done with the employee there: no message by default.
  notify.value = r.origin !== 'direct'
  // The date set when confirming; the employee is told this one with the ready message.
  // Without one, the next full hour; licenses alone need no date.
  when.value = r.pickup_at
    ? new Date(r.pickup_at).getTime()
    : hasPhysical.value
      ? nextFullHour()
      : null
  where.value = r.pickup_location?.id ?? null
  whereInitial.value = (r.pickup_location as Schemas['LocationOut'] | null) ?? null
  if (!where.value && hasPhysical.value) {
    const only = await onlyPickupPoint()
    if (only && !where.value) {
      where.value = only.id
      whereInitial.value = only
    }
  }
})

/** Only devices and consumables are collected; a request of licenses alone is handed out at once. */
const hasPhysical = computed(() =>
  props.assetRequest.items.some((i) => i.allocations.some((a) => Boolean(a.asset ?? a.consumable))),
)
/** The ready message tells when and, unless IT delivers, where. */
const needsWhen = computed(() => notify.value && hasPhysical.value)
const needsWhere = computed(() => needsWhen.value && mode.value !== 'delivery')
const incomplete = computed(
  () => (needsWhen.value && !when.value) || (needsWhere.value && !where.value),
)

async function save() {
  const saved = await run(() =>
    requestsApi.markReady(props.assetRequest.id, {
      handover_mode: mode.value,
      skip_device_check: mode.value === 'pickup' && skipCheck.value,
      pickup_at: when.value ? new Date(when.value).toISOString() : null,
      pickup_location: where.value,
      notify: notify.value,
    }),
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
        :required="needsWhen"
        :show-feedback="false"
      >
        <div class="when">
          <DateTimeField v-model:value="when" clearable />
          <small v-if="assetRequest.requested_pickup_date" class="muted wish">{{
            t('requests.wishHint', { date: weekday(assetRequest.requested_pickup_date) })
          }}</small>
        </div>
      </NFormItem>
      <NFormItem
        v-if="mode !== 'delivery'"
        :label="t('requests.pickupLocation')"
        :required="needsWhere"
        :show-feedback="false"
      >
        <EntitySelect
          v-model="where"
          :fetcher="locationsApi.list"
          :params="{ is_pickup_point: true }"
          :label="(l) => l.full_name"
          :initial="whereInitial as never"
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
        <small v-if="incomplete" class="muted missing">{{
          mode === 'delivery' ? t('handover.planMissingDelivery') : t('handover.planMissing')
        }}</small>
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" :disabled="incomplete" @click="save">{{
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
.missing {
  margin-right: auto;
}
</style>
