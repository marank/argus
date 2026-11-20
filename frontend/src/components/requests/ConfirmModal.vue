<script setup lang="ts">
import type { Id } from '@/types/common'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NModal, NSwitch, NTable } from 'naive-ui'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { locationsApi } from '@/api/masterdata'
import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import DateTimeField from '@/components/common/DateTimeField.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { itemLabel, nextFullHour } from '@/utils/requests'

import HandoverModeSelect from './HandoverModeSelect.vue'
import { onlyPickupPoint } from './pickupPoint'

/**
 * `confirm`: tell the employee the request is fine, possibly with fewer devices; editing a
 * confirmed request keeps what is already allocated. `schedule`: change how, when and where
 * the devices reach the employee once it is ready.
 */
const props = defineProps<{
  assetRequest: Schemas['AssetRequestOut']
  mode: 'confirm' | 'schedule'
}>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()
const { weekday } = useFormat()
const { busy, run } = useAction()
/**
 * Changing the quantities of a request that is already confirmed. Fixed when the dialog
 * opens: confirming turns the request confirmed while the dialog still fades out.
 */
const editing = ref(false)

const form = reactive({
  quantities: {} as Record<Id, number>,
  pickup_at: null as number | null,
  pickup_location: null as Id | null,
  comment: '',
  handover_mode: 'pickup' as Schemas['HandoverMode'],
  notify: true,
})

function defaultPickup(): number {
  const day = props.assetRequest.requested_pickup_date ?? props.assetRequest.start_date
  const start = new Date(`${day}T09:00:00`)
  return Math.max(start.getTime(), nextFullHour())
}
/** The location shown before the list has loaded: the planned one or the only one there is. */
const locationInitial = ref<Schemas['LocationOut'] | null>(null)

watch(show, async (visible) => {
  if (!visible) return
  const r = props.assetRequest
  editing.value = r.status === 'confirmed'
  form.quantities = Object.fromEntries(
    r.items.map((i) => [i.id, i.quantity_confirmed ?? i.quantity_requested]),
  )
  form.pickup_at = r.pickup_at ? new Date(r.pickup_at).getTime() : defaultPickup()
  form.pickup_location = r.pickup_location?.id ?? null
  form.comment = r.it_comment
  form.handover_mode = r.handover_mode
  // As when marking it ready: a direct hand-out is usually done with the employee there.
  form.notify = r.origin !== 'direct'
  locationInitial.value = (r.pickup_location as Schemas['LocationOut'] | null) ?? null
  if (props.mode === 'schedule' && !form.pickup_location) {
    const only = await onlyPickupPoint()
    if (only && !form.pickup_location) {
      form.pickup_location = only.id
      locationInitial.value = only
    }
  }
})

/** Once the employee was told it is ready, a new message needs when and, unless IT delivers, where. */
const needsWhen = computed(
  () => props.mode === 'schedule' && props.assetRequest.status === 'ready' && form.notify,
)
const needsWhere = computed(() => needsWhen.value && form.handover_mode !== 'delivery')
const incomplete = computed(
  () => (needsWhen.value && !form.pickup_at) || (needsWhere.value && !form.pickup_location),
)

async function save() {
  const pickup_at = form.pickup_at ? new Date(form.pickup_at).toISOString() : null
  const saved = await run(() =>
    props.mode === 'confirm'
      ? requestsApi.confirm(props.assetRequest.id, {
          items: Object.entries(form.quantities).map(([id, quantity]) => ({
            id,
            quantity_confirmed: quantity,
          })),
          comment: form.comment,
        })
      : requestsApi.schedule(props.assetRequest.id, {
          pickup_at,
          pickup_location: form.pickup_location,
          handover_mode: form.handover_mode,
          notify: form.notify,
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
    :title="
      mode === 'schedule'
        ? t('requests.actions.schedule')
        : editing
          ? t('requests.confirming.editTitle')
          : t('requests.actions.confirmTitle')
    "
    style="max-width: 720px"
  >
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <template v-if="mode === 'confirm'">
        <p class="muted">
          {{ editing ? t('requests.confirming.editHint') : t('requests.actions.confirmHint') }}
        </p>
        <NTable size="small" :bordered="false" class="items">
          <thead>
            <tr>
              <th>{{ t('requests.items') }}</th>
              <th class="num">{{ t('requests.quantities.requested') }}</th>
              <th class="num">{{ t('requests.quantities.confirmed') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in assetRequest.items" :key="item.id">
              <td>
                {{ itemLabel(item) }}
                <div v-if="item.note" class="muted small">{{ item.note }}</div>
                <div v-if="item.quantity_allocated" class="muted small">
                  {{ t('requests.confirming.allocated', { count: item.quantity_allocated }) }}
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
        <NFormItem :label="t('requests.itComment')">
          <NInput
            v-model:value="form.comment"
            type="textarea"
            :autosize="{ minRows: 2, maxRows: 5 }"
          />
        </NFormItem>
      </template>
      <div v-else class="cols">
        <NFormItem :label="t('requests.pickupAt')" :required="needsWhen">
          <div class="when">
            <DateTimeField v-model:value="form.pickup_at" clearable />
            <small v-if="assetRequest.requested_pickup_date" class="muted wish">{{
              t('requests.wishHint', { date: weekday(assetRequest.requested_pickup_date) })
            }}</small>
          </div>
        </NFormItem>
        <NFormItem :label="t('requests.pickupLocation')" :required="needsWhere">
          <EntitySelect
            v-model="form.pickup_location"
            :fetcher="locationsApi.list"
            :params="{ is_pickup_point: true }"
            :label="(l) => l.full_name"
            :initial="locationInitial as never"
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
        <small v-if="incomplete" class="muted missing">{{
          form.handover_mode === 'delivery'
            ? t('handover.planMissingDelivery')
            : t('handover.planMissing')
        }}</small>
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" :disabled="incomplete" @click="save">
          {{ mode === 'confirm' && !editing ? t('requests.actions.confirm') : t('common.save') }}
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
.missing {
  margin-right: auto;
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
