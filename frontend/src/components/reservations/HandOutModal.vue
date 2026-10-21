<script setup lang="ts">
import type { Id } from '@/types/common'
import { NButton, NForm, NFormItem, NInput, NModal, NRadioButton, NRadioGroup } from 'naive-ui'
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { usersApi } from '@/api/accounts'
import { reservationsApi } from '@/api/reservations'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'
import type { Reservation } from '@/types/reservations'
import { allocationCode, allocationModel } from '@/utils/reservations'

/** Hand-out documented by IT without signature: collected at the desk or delivered. */
const props = defineProps<{ reservation: Reservation }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [reservation: Reservation] }>()
const { t } = useI18n()
const { busy, run } = useAction()

const form = reactive({
  method: 'direct' as 'direct' | 'delivered',
  received_by: null as Id | null,
  location: '',
  notes: '',
  allocationNotes: {} as Record<Id, string>,
})

const allocations = computed(() => props.reservation.items.flatMap((item) => item.allocations))

watch(show, (visible) => {
  if (!visible) return
  Object.assign(form, {
    method: props.reservation.handover_mode === 'delivery' ? 'delivered' : 'direct',
    received_by: props.reservation.requester.id,
    location: '',
    notes: '',
    allocationNotes: {},
  })
})

async function save() {
  const saved = await run(
    () =>
      reservationsApi.handOut(props.reservation.id, {
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
    :title="t('reservations.actions.handOut')"
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
            :params="{ is_active: true }"
            :label="(u) => u.display_name"
            :initial="reservation.requester as never"
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
          {{ t('reservations.actions.handOut') }}
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
