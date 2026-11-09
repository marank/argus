<script setup lang="ts">
import { ScanLine } from '@lucide/vue'
import { NInput, NModal, NList, NListItem, useMessage } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { lookupApi } from '@/api/inventory'
import StatusTag from '@/components/common/StatusTag.vue'
import { showError } from '@/composables/useErrorPopover'
import { useScanner } from '@/composables/useScanner'
import type { Schemas } from '@/api/types'

/**
 * Scan field in the top bar. Works with keyboard-wedge scanners even when the
 * field is not focused: a scan anywhere jumps to the device or model.
 */
const { t } = useI18n()
const router = useRouter()
const message = useMessage()

const code = ref('')
const field = ref<{ $el: HTMLElement } | null>(null)
const result = ref<Schemas['LookupOut'] | null>(null)
const showResults = ref(false)

async function lookup(value: string) {
  const trimmed = value.trim()
  if (!trimmed) return
  let found: Schemas['LookupOut']
  try {
    found = await lookupApi.lookup(trimmed)
  } catch (error) {
    // The code stays in the field, so the user can try again.
    showError(error instanceof Error ? error.message : t('common.error'), field.value?.$el)
    return
  }
  code.value = ''
  if (found.kind === 'asset') {
    router.push({ name: 'asset', params: { id: found.assets[0]!.id } })
  } else if (found.kind === 'model') {
    router.push({ name: 'assets', query: { model: found.models[0]!.id } })
  } else if (found.kind === 'multiple') {
    result.value = found
    showResults.value = true
    message.info(
      t('common.scanMultiple', { count: found.assets.length + found.models.length, code: trimmed }),
    )
  } else {
    showError(t('common.scanNotFound', { code: trimmed }), field.value?.$el)
  }
}

function open(to: Parameters<typeof router.push>[0]) {
  showResults.value = false
  router.push(to)
}

useScanner(lookup)
</script>

<template>
  <NInput
    ref="field"
    v-model:value="code"
    class="scan"
    size="small"
    :placeholder="t('common.scanPlaceholder')"
    clearable
    @keydown.enter.prevent="lookup(code)"
  >
    <template #prefix><ScanLine :size="15" /></template>
  </NInput>

  <NModal
    v-model:show="showResults"
    preset="card"
    :title="t('common.scan')"
    style="max-width: 560px"
  >
    <NList hoverable clickable>
      <NListItem
        v-for="asset in result?.assets"
        :key="`a${asset.id}`"
        @click="open({ name: 'asset', params: { id: asset.id } })"
      >
        <div class="row">
          <span class="mono">{{ asset.inventory_number }}</span>
          <span>{{ asset.model.full_name }}</span>
          <span class="mono muted">{{ asset.serial_number }}</span>
          <StatusTag group="assetStatus" :value="asset.status" style="margin-left: auto" />
        </div>
      </NListItem>
      <NListItem
        v-for="model in result?.models"
        :key="`m${model.id}`"
        @click="open({ name: 'assets', query: { model: model.id } })"
      >
        <div class="row">
          <span class="mono">{{ model.ean }}</span>
          <span>{{ model.full_name }}</span>
        </div>
      </NListItem>
    </NList>
  </NModal>
</template>

<style scoped>
.scan {
  max-width: 420px;
}
.scan :deep(input) {
  font-family: var(--ar-font-mono);
  font-size: 12px;
}
</style>
