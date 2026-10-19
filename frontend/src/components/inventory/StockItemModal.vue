<script setup lang="ts">
import type { Id } from '@/types/common'
import { NButton, NForm, NFormItem, NInputNumber, NModal } from 'naive-ui'
import { reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { stockApi } from '@/api/inventory'
import { assetModelsApi, locationsApi } from '@/api/masterdata'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { useAction } from '@/composables/useAction'
import type { StockItem } from '@/types/inventory'

const props = defineProps<{ item: StockItem | null }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ saved: [] }>()
const { t } = useI18n()
const { busy, run } = useAction()

const form = reactive({
  model: null as Id | null,
  location: null as Id | null,
  min_quantity: 0,
})

watch(show, (visible) => {
  if (!visible) return
  Object.assign(form, {
    model: props.item?.model.id ?? null,
    location: props.item?.location.id ?? null,
    min_quantity: props.item?.min_quantity ?? 0,
  })
})

async function save() {
  const ok = await run(
    () =>
      props.item
        ? stockApi.update(props.item.id, { min_quantity: form.min_quantity })
        : stockApi.create({
            model: form.model!,
            location: form.location!,
            min_quantity: form.min_quantity,
          }),
    t('common.saved'),
  )
  if (ok) {
    show.value = false
    emit('saved')
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="item ? item.model.full_name : t('inventory.stock.newItem')"
    style="max-width: 460px"
  >
    <NForm class="ar-form" label-placement="top" size="small" :show-feedback="false">
      <NFormItem>
        <template #label><FieldLabel :label="t('inventory.fields.model')" required /></template>
        <EntitySelect
          v-model="form.model"
          :fetcher="assetModelsApi.list"
          :params="{ tracking: 'bulk' }"
          :label="(m) => m.full_name"
          :disabled="!!item"
          :initial="item?.model as never"
        />
      </NFormItem>
      <NFormItem>
        <template #label><FieldLabel :label="t('inventory.fields.location')" required /></template>
        <EntitySelect
          v-model="form.location"
          :fetcher="locationsApi.list"
          :label="(l) => l.full_name"
          :disabled="!!item"
          :initial="item?.location as never"
        />
      </NFormItem>
      <NFormItem :label="t('inventory.stock.minimum')">
        <NInputNumber v-model:value="form.min_quantity" :min="0" style="width: 100%" />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton
          type="primary"
          :loading="busy"
          :disabled="!form.model || !form.location"
          @click="save"
          >{{ t('common.save') }}</NButton
        >
      </div>
    </template>
  </NModal>
</template>
