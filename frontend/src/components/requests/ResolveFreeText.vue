<script setup lang="ts">
import { Link2, MessageSquarePlus, Plus } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { assetModelsApi } from '@/api/masterdata'
import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'
import type { Id } from '@/types/common'
import { modelLabel } from '@/utils/models'

import CreateModelModal from './CreateModelModal.vue'

/** Decision panel for a free-text line: create a new model or map an existing one. */
const props = defineProps<{
  assetRequest: Schemas['AssetRequestOut']
  item: Schemas['AssetRequestItemOut']
}>()
const emit = defineEmits<{ updated: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()
const { busy, run } = useAction()

const showCreate = ref(false)
const existing = ref<Id | null>(null)

async function assign() {
  if (!existing.value) return
  const updated = await run(() =>
    requestsApi.resolveItem(props.assetRequest.id, props.item.id, existing.value!),
  )
  if (updated) emit('updated', updated)
}
</script>

<template>
  <div class="resolve">
    <div class="head">
      <MessageSquarePlus :size="15" />
      <span>{{ t('requests.freeTextResolve.hint') }}</span>
    </div>
    <div class="actions">
      <NButton size="small" type="primary" secondary @click="showCreate = true">
        <template #icon><Plus :size="14" /></template>
        {{ t('requests.freeTextResolve.create') }}
      </NButton>
      <span class="muted">{{ t('requests.freeTextResolve.or') }}</span>
      <EntitySelect
        v-model="existing"
        size="small"
        class="select"
        :fetcher="assetModelsApi.list"
        :params="
          item.category ? { category: item.category.id, is_active: true } : { is_active: true }
        "
        :label="modelLabel"
        :placeholder="t('requests.freeTextResolve.existing')"
      />
      <NButton size="small" :disabled="!existing" :loading="busy" @click="assign">
        <template #icon><Link2 :size="14" /></template>
        {{ t('requests.freeTextResolve.assign') }}
      </NButton>
    </div>
    <CreateModelModal
      v-model:show="showCreate"
      :asset-request="assetRequest"
      :item="item"
      @saved="(r) => emit('updated', r)"
    />
  </div>
</template>

<style scoped>
.resolve {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border: 1px dashed var(--ar-warning);
  border-radius: 3px;
  background: color-mix(in srgb, var(--ar-warning) 6%, transparent);
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ar-warning);
  font-size: 12px;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}
.select {
  flex: 1 1 220px;
}
</style>
