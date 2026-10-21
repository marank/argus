<script setup lang="ts">
import type { Id } from '@/types/common'
import { NButton, NForm, NFormItem, NInput, NModal, NSelect, useMessage } from 'naive-ui'
import { computed, reactive, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { assetsApi } from '@/api/inventory'
import { assetModelsApi, locationsApi, suppliersApi } from '@/api/masterdata'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { ASSET_CONDITIONS, type AssetCondition } from '@/types/inventory'

const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ created: [] }>()
const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()
const message = useMessage()

const form = reactive({
  model: null as Id | null,
  location: null as Id | null,
  supplier: null as Id | null,
  condition: 'new' as AssetCondition,
})
const serialText = ref('')

const serials = computed(() =>
  serialText.value
    .split(/[\n,;\t]+/)
    .map((s) => s.trim())
    .filter(Boolean),
)

async function submit() {
  const created = await run(() => assetsApi.bulkCreate({ ...form, serial_numbers: serials.value }))
  if (created) {
    serialText.value = ''
    show.value = false
    emit('created')
    message.success(t('inventory.bulk.created', { count: created.length }))
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t('inventory.bulk.title')"
    style="max-width: 640px"
  >
    <p class="muted">{{ t('inventory.bulk.help') }}</p>
    <NForm class="ar-form" label-placement="top" size="medium" :show-feedback="false">
      <NFormItem>
        <template #label><FieldLabel :label="t('inventory.fields.model')" required /></template>
        <EntitySelect
          v-model="form.model"
          :fetcher="assetModelsApi.list"
          :params="{ tracking: 'serialized' }"
          :label="(m) => m.full_name"
        />
      </NFormItem>
      <div class="cols">
        <NFormItem :label="t('inventory.fields.location')">
          <EntitySelect
            v-model="form.location"
            :fetcher="locationsApi.list"
            :label="(l) => l.full_name"
          />
        </NFormItem>
        <NFormItem :label="t('inventory.fields.supplier')">
          <EntitySelect
            v-model="form.supplier"
            :fetcher="suppliersApi.list"
            :label="(s) => s.name"
          />
        </NFormItem>
        <NFormItem :label="t('inventory.fields.condition')">
          <NSelect
            v-model:value="form.condition"
            :options="ASSET_CONDITIONS.map((c) => ({ value: c, label: enumLabel('condition', c) }))"
          />
        </NFormItem>
      </div>
      <NFormItem>
        <template #label>
          <FieldLabel :label="t('inventory.bulk.serials')">
            <template #extra>{{ t('inventory.bulk.count', { count: serials.length }) }}</template>
          </FieldLabel>
        </template>
        <NInput
          v-model:value="serialText"
          type="textarea"
          class="serials"
          :autosize="{ minRows: 8, maxRows: 16 }"
          autofocus
        />
      </NFormItem>
    </NForm>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton
          type="primary"
          :disabled="!form.model || !serials.length"
          :loading="busy"
          @click="submit"
        >
          {{ t('common.create') }} ({{ serials.length }})
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.cols {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.serials :deep(textarea) {
  font-family: var(--ar-font-mono);
  font-size: 12px;
}
</style>
