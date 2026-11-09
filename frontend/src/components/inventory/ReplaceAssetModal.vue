<script setup lang="ts">
import { NButton, NCheckbox, NFormItem, NModal, NRadioButton, NRadioGroup } from 'naive-ui'
import { computed, reactive, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { assetsApi } from '@/api/inventory'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import type { Id } from '@/types/common'
import { modelLabel } from '@/utils/models'

/**
 * Put a device from stock in this one's place, e.g. a new PC that keeps the old hostname or a
 * spare MDE for one in repair: the replacement takes over the device name, the holder and the
 * location; this device goes into stock, into repair or is retired.
 */
const props = defineProps<{ asset: Schemas['AssetDetailOut'] }>()
const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ replaced: [replacement: Schemas['AssetDetailOut']] }>()
const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

const STATUSES: Schemas['AssetStatus'][] = ['in_stock', 'in_repair', 'retired']

const form = reactive({
  replacement: null as Id | null,
  status: 'in_repair' as Schemas['AssetStatus'],
  anyCategory: false,
})

watch(show, (visible) => {
  if (visible) Object.assign(form, { replacement: null, status: 'in_repair', anyCategory: false })
})

const params = computed(() => ({
  status: 'in_stock',
  // The same kind of device: not its accessories in subcategories.
  own_category: form.anyCategory ? undefined : props.asset.category.id,
}))
const label = (a: Schemas['AssetOut']) =>
  [a.inventory_number, a.name, modelLabel(a.model), a.serial_number].filter(Boolean).join(' · ')

async function save() {
  const replacement = await run(
    () =>
      assetsApi.replace(props.asset.id, { replacement: form.replacement!, status: form.status }),
    t('inventory.replace.saved'),
  )
  if (replacement) {
    show.value = false
    emit('replaced', replacement)
  }
}
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t('inventory.replace.title')"
    style="max-width: 480px"
  >
    <p class="muted hint">
      {{
        asset.name
          ? t('inventory.replace.hint', { name: asset.name })
          : t('inventory.replace.hintWithoutName')
      }}
    </p>
    <div class="fields">
      <NFormItem :label="t('inventory.replace.replacement')" :show-feedback="false">
        <div class="stack">
          <EntitySelect
            v-model="form.replacement"
            :fetcher="assetsApi.list"
            :params="params"
            :label="label"
          />
          <NCheckbox v-model:checked="form.anyCategory">
            {{ t('inventory.replace.anyCategory') }}
          </NCheckbox>
        </div>
      </NFormItem>
      <NFormItem :label="t('inventory.replace.oldStatus')" :show-feedback="false">
        <NRadioGroup v-model:value="form.status" class="statuses">
          <NRadioButton v-for="status in STATUSES" :key="status" :value="status">
            {{ enumLabel('assetStatus', status) }}
          </NRadioButton>
        </NRadioGroup>
      </NFormItem>
    </div>
    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        <NButton type="primary" :disabled="!form.replacement" :loading="busy" @click="save">
          {{ t('inventory.replace.submit') }}
        </NButton>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.hint {
  margin: 0 0 14px;
}
.fields {
  display: grid;
  gap: 14px;
}
.stack {
  display: grid;
  gap: 8px;
  width: 100%;
}
.statuses {
  display: flex;
  width: 100%;
}
.statuses :deep(.n-radio-button) {
  flex: 1;
  text-align: center;
}
</style>
