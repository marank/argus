<script setup lang="ts">
import type { Id } from '@/types/common'
import { NButton, NForm, NFormItem, NInput, NInputNumber, NModal, NSelect } from 'naive-ui'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { assetsApi, consumablesApi } from '@/api/inventory'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import ToggleRow from '@/components/common/ToggleRow.vue'
import DateField from '@/components/common/DateField.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { MANUAL_EVENT_KINDS } from '@/types/inventory'
import { useFeaturesStore } from '@/stores/features'

const props = defineProps<{ assetId: Id }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n()
const features = useFeaturesStore()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

const form = reactive({
  kind: 'battery_replaced' as Schemas['AssetEventKind'],
  occurred_at: Date.now(),
  description: '',
  component: '',
  component_serial: '',
  cost: null as number | null,
})
const consume = ref(false)
const consumable = ref<Id | null>(null)
const quantity = ref(1)

watch(show, (visible) => {
  if (visible)
    Object.assign(form, {
      occurred_at: Date.now(),
      description: '',
      component: '',
      component_serial: '',
      cost: null,
    })
})

const kindOptions = computed(() =>
  MANUAL_EVENT_KINDS.map((k) => ({ value: k, label: enumLabel('eventKind', k) })),
)
const hasComponent = computed(() =>
  ['battery_replaced', 'component_replaced', 'repair'].includes(form.kind),
)

async function save() {
  const done = await run(
    () =>
      assetsApi.addEvent(props.assetId, {
        ...form,
        occurred_at: new Date(form.occurred_at).toISOString(),
        cost: form.cost === null ? null : form.cost.toFixed(2),
        consume:
          consume.value && consumable.value
            ? { consumable_id: consumable.value, quantity: quantity.value }
            : null,
      }),
    t('common.saved'),
  )
  if (done) {
    show.value = false
    emit('saved')
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t('inventory.recordEvent')"
    style="max-width: 560px"
  >
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <div class="cols">
        <NFormItem :label="t('inventory.event.kind')">
          <NSelect v-model:value="form.kind" :options="kindOptions" />
        </NFormItem>
        <NFormItem :label="t('inventory.event.occurredAt')">
          <DateField v-model:value="form.occurred_at" type="datetime" style="width: 100%" />
        </NFormItem>
        <template v-if="hasComponent">
          <NFormItem :label="t('inventory.event.component')">
            <NInput v-model:value="form.component" />
          </NFormItem>
          <NFormItem :label="t('inventory.event.componentSerial')">
            <NInput v-model:value="form.component_serial" />
          </NFormItem>
        </template>
        <NFormItem :label="t('inventory.event.cost')">
          <NInputNumber v-model:value="form.cost" :precision="2" :min="0" style="width: 100%">
            <template #suffix>€</template>
          </NInputNumber>
        </NFormItem>
      </div>
      <NFormItem :label="t('common.description')">
        <NInput
          v-model:value="form.description"
          type="textarea"
          :autosize="{ minRows: 2, maxRows: 6 }"
        />
      </NFormItem>
      <ToggleRow
        v-if="features.isOn('consumables')"
        v-model="consume"
        class="consume-toggle"
        :label="t('inventory.event.consume')"
      />
      <div v-if="consume" class="cols consume">
        <NFormItem :label="t('inventory.event.consumeItem')">
          <EntitySelect
            v-model="consumable"
            :fetcher="consumablesApi.list"
            :label="(s) => `${s.model.full_name} · ${s.location.name} (${s.available_quantity})`"
          />
        </NFormItem>
        <NFormItem :label="t('common.quantity')">
          <NInputNumber v-model:value="quantity" :min="1" style="width: 100%" />
        </NFormItem>
      </div>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" @click="save">{{ t('common.save') }}</NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.cols {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 12px;
}
.consume-toggle {
  margin-top: 6px;
}
/* The fields the switch reveals, indented below it like in the master data forms. */
.consume {
  padding-left: 12px;
  border-left: 2px solid var(--ar-primary-soft);
}
</style>
