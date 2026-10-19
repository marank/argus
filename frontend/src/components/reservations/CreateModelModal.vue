<script setup lang="ts">
import { NButton, NForm, NFormItem, NInput, NModal, NSelect } from 'naive-ui'
import { reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { assetModelsApi, categoriesApi, manufacturersApi } from '@/api/masterdata'
import { reservationsApi } from '@/api/reservations'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import type { Id } from '@/types/common'
import type { Tracking } from '@/types/masterdata'
import type { Reservation, ReservationItem } from '@/types/reservations'

/** Create a catalog model from a free-text line and assign it right away. */
const props = defineProps<{ reservation: Reservation; item: ReservationItem }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [reservation: Reservation] }>()
const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

const form = reactive({
  name: '',
  manufacturer: null as Id | null,
  category: null as Id | null,
  tracking: 'serialized' as Tracking,
  part_number: '',
})

watch(show, (visible) => {
  if (!visible) return
  Object.assign(form, {
    name: props.item.description,
    manufacturer: null,
    category: props.item.category?.id ?? null,
    tracking: 'serialized',
    part_number: '',
  })
})

async function save() {
  const reservation = await run(async () => {
    const model = await assetModelsApi.create({ ...form, compatible_with: [] } as never)
    return reservationsApi.resolveItem(props.reservation.id, props.item.id, model.id)
  }, t('common.saved'))
  if (reservation) {
    show.value = false
    emit('saved', reservation)
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t('reservations.freeTextResolve.createTitle')"
    style="max-width: 560px"
  >
    <p class="muted">{{ t('reservations.freeTextResolve.createHint') }}</p>
    <NForm class="ar-form" label-placement="top" size="small" :show-feedback="false">
      <NFormItem>
        <template #label><FieldLabel :label="t('common.name')" required /></template>
        <NInput v-model:value="form.name" />
      </NFormItem>
      <div class="cols">
        <NFormItem>
          <template #label
            ><FieldLabel :label="t('masterdata.fields.manufacturer')" required
          /></template>
          <EntitySelect
            v-model="form.manufacturer"
            :fetcher="manufacturersApi.list"
            :label="(m) => m.name"
          />
        </NFormItem>
        <NFormItem>
          <template #label
            ><FieldLabel :label="t('masterdata.fields.category')" required
          /></template>
          <EntitySelect
            v-model="form.category"
            :fetcher="categoriesApi.list"
            :label="(c) => c.path.join(' / ')"
            :initial="
              item.category ? ({ ...item.category, path: [item.category.name] } as never) : null
            "
          />
        </NFormItem>
        <NFormItem>
          <template #label>
            <FieldLabel
              :label="t('masterdata.fields.tracking')"
              :help="t('masterdata.fields.trackingHelp')"
            />
          </template>
          <NSelect
            v-model:value="form.tracking"
            :options="
              (['serialized', 'bulk'] as const).map((v) => ({
                value: v,
                label: enumLabel('tracking', v),
              }))
            "
          />
        </NFormItem>
        <NFormItem :label="t('masterdata.fields.partNumber')">
          <NInput v-model:value="form.part_number" class="mono-input" />
        </NFormItem>
      </div>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton
          type="primary"
          :loading="busy"
          :disabled="!form.name.trim() || !form.manufacturer || !form.category"
          @click="save"
        >
          {{ t('reservations.freeTextResolve.createAndAssign') }}
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
.mono-input :deep(input) {
  font-family: var(--ar-font-mono);
}
</style>
