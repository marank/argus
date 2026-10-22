<script setup lang="ts">
import type { Id } from '@/types/common'
import { NButton, NForm, NFormItem, NInput, NModal, NRadioButton, NRadioGroup } from 'naive-ui'
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import { requestsApi } from '@/api/requests'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'
import type { AssetRequest } from '@/types/requests'
import { allocationCode, allocationModel } from '@/utils/requests'

/** Hand-out documented by IT without signature: collected at the desk or delivered. */
const props = defineProps<{ assetRequest: AssetRequest }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [assetRequest: AssetRequest] }>()
const { t } = useI18n()
const { busy, run } = useAction()

const form = reactive({
  method: 'direct' as 'direct' | 'delivered',
  received_by: null as Id | null,
  location: '',
  notes: '',
  allocationNotes: {} as Record<Id, string>,
})

const allocations = computed(() => props.assetRequest.items.flatMap((item) => item.allocations))

watch(show, (visible) => {
  if (!visible) return
  Object.assign(form, {
    method: props.assetRequest.handover_mode === 'delivery' ? 'delivered' : 'direct',
    received_by: props.assetRequest.requester.id,
    location: '',
    notes: '',
    allocationNotes: {},
  })
})

async function save() {
  const saved = await run(
    () =>
      requestsApi.handOut(props.assetRequest.id, {
        method: form.method,
        received_by: form.received_by,
        received_by_name: '',
        location: form.method === 'delivered' ? form.location : '',
        notes: form.notes,
        allocation_notes: Object.entries(form.allocationNotes)
          .filter(([, note]) => note.trim())
          .map(([allocation, note]) => ({ allocation, note })),
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
    :title="t('requests.actions.handOut')"
    style="max-width: 640px"
  >
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <NFormItem :label="t('handover.method')">
        <NRadioGroup v-model:value="form.method">
          <NRadioButton value="direct">{{ t('enums.handoverMethod.direct') }}</NRadioButton>
          <NRadioButton value="delivered">{{ t('enums.handoverMethod.delivered') }}</NRadioButton>
        </NRadioGroup>
      </NFormItem>
      <div class="cols">
        <NFormItem :label="t('handover.receivedBy')">
          <EntitySelect
            v-model="form.received_by"
            :fetcher="usersApi.list"
            :params="{ is_active: true, is_terminal: false }"
            :label="(u) => u.display_name"
            :initial="assetRequest.requester as never"
            :clearable="false"
          />
        </NFormItem>
        <NFormItem v-if="form.method === 'delivered'" :label="t('handover.deliveredTo')">
          <NInput
            v-model:value="form.location"
            :placeholder="t('handover.deliveredToPlaceholder')"
          />
        </NFormItem>
      </div>
      <div class="eyebrow">{{ t('handover.deviceNotes') }}</div>
      <div v-for="allocation in allocations" :key="allocation.id" class="device">
        <span class="mono">{{ allocationCode(allocation) }}</span>
        <span class="name">{{ allocationModel(allocation) }}</span>
        <NInput
          v-model:value="form.allocationNotes[allocation.id]"
          size="small"
          :placeholder="t('handover.deviceNotePlaceholder')"
        />
      </div>
      <NFormItem :label="t('common.notes')" class="notes">
        <NInput v-model:value="form.notes" type="textarea" :autosize="{ minRows: 2, maxRows: 5 }" />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :loading="busy" :disabled="!form.received_by" @click="save">
          {{ t('requests.actions.handOut') }}
        </NButton>
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
.device {
  display: grid;
  grid-template-columns: 100px minmax(0, 1fr) minmax(0, 1.2fr);
  gap: 10px;
  align-items: center;
  padding: 4px 0;
}
.name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.eyebrow {
  margin-bottom: 4px;
}
.notes {
  margin-top: 12px;
}
</style>
