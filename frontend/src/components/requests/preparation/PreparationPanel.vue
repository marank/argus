<script setup lang="ts">
import type { Id } from '@/types/common'
import { Sparkles } from '@lucide/vue'
import { NButton, NCard, useMessage } from 'naive-ui'
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import { useAction } from '@/composables/useAction'

import PreparationLine from './PreparationLine.vue'
import PreparationScan from './PreparationScan.vue'

/**
 * The lines of a request with what is allocated to them. While preparing (or recording
 * devices after a hand-out without them) one scan field fills all lines; otherwise it
 * only shows what the request holds.
 */
const props = defineProps<{
  assetRequest: Schemas['AssetRequestOut']
  /** Preparing: devices can be allocated and removed. */
  editable: boolean
  /** Recording devices after a hand-out without them. */
  recording?: boolean
  /** Pool counts for the request's period, shown before IT confirms. */
  availability?: (item: Schemas['AssetRequestItemOut']) => Schemas['CountsOut'] | null
}>()
const emit = defineEmits<{ updated: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()
const { busy, run } = useAction()
const message = useMessage()

const highlight = ref<Id | null>(null)
const pool = ref<Record<Id, number>>({})

const items = computed(() => props.assetRequest.items)
const target = (i: Schemas['AssetRequestItemOut']) => i.quantity_confirmed ?? i.quantity_requested
const total = computed(() => items.value.reduce((sum, i) => sum + target(i), 0))
const done = computed(() =>
  items.value.reduce((sum, i) => sum + Math.min(i.quantity_allocated, target(i)), 0),
)
const isConsumable = (i: Schemas['AssetRequestItemOut']) =>
  i.asset_model?.tracking === 'bulk' || i.allocations.some((a) => a.consumable)
/** Lines the scan field can fill: devices still missing, model known. */
const scannable = computed(
  () =>
    props.editable &&
    items.value.some(
      (i) => i.quantity_missing && !i.is_free_text && !i.is_software && !isConsumable(i),
    ),
)
/** Lines "Allocate automatically" can fill from the pool. */
const autoLines = computed(() =>
  props.editable && props.assetRequest.status === 'confirmed'
    ? items.value.filter(
        (i) => i.quantity_missing && !i.is_free_text && !isConsumable(i) && (pool.value[i.id] ?? 0),
      )
    : [],
)

const title = computed(() =>
  props.recording
    ? t('requests.unrecorded.title')
    : props.editable
      ? t('requests.allocation.title')
      : t('requests.items'),
)

/** How many devices or seats the pool holds per open line, again after every change. */
async function loadPool() {
  try {
    const result = await requestsApi.lineCandidates(props.assetRequest.id)
    pool.value = Object.fromEntries(result.pool.map((p) => [p.item, p.available]))
  } catch {
    pool.value = {}
  }
}
watch(
  () => [props.editable, props.assetRequest] as const,
  ([editable]) => editable && props.assetRequest.status === 'confirmed' && loadPool(),
  { immediate: true },
)

function updated(
  assetRequest: Schemas['AssetRequestOut'],
  added?: Schemas['AllocationOut'] | null,
) {
  clearTimeout(fading)
  highlight.value = added?.id ?? null
  // Only a moment's notice: the row then looks like every other.
  if (highlight.value) fading = setTimeout(() => (highlight.value = null), HIGHLIGHT_MS)
  emit('updated', assetRequest)
}

const HIGHLIGHT_MS = 3000
let fading: ReturnType<typeof setTimeout> | undefined
onBeforeUnmount(() => clearTimeout(fading))

async function allocateAll() {
  const result = await run(() => requestsApi.autoAllocate(props.assetRequest.id))
  if (!result) return
  message.info(t('requests.actions.autoAllocated', { count: result.allocated }, result.allocated))
  updated(result.asset_request)
}
</script>

<template>
  <NCard :title="title" size="small" class="preparation">
    <template v-if="editable" #header-extra>
      <div class="progress">
        <span class="muted">{{ t('requests.preparation.progress', { done, total }) }}</span>
        <span class="bar"
          ><span :style="{ width: `${total ? (done / total) * 100 : 100}%` }"
        /></span>
        <NButton
          v-if="autoLines.length > 1"
          size="tiny"
          secondary
          :loading="busy"
          @click="allocateAll"
        >
          <template #icon><Sparkles :size="13" /></template>
          {{ t('requests.preparation.allocateAll') }}
        </NButton>
      </div>
    </template>
    <p v-if="recording" class="muted hint">{{ t('requests.unrecorded.hint') }}</p>
    <PreparationScan v-if="scannable" :assetRequest="assetRequest" @updated="updated" />
    <PreparationLine
      v-for="item in items"
      :key="item.id"
      :assetRequest="assetRequest"
      :item="item"
      :editable="editable"
      :pool="pool[item.id]"
      :highlight="highlight"
      :availability="availability?.(item) ?? null"
      @updated="(r) => updated(r)"
    />
  </NCard>
</template>

<style scoped>
.progress {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 12px;
}
.bar {
  width: 96px;
  height: 4px;
  border-radius: 2px;
  background: var(--ar-surface-sunken);
  overflow: hidden;
}
.bar > span {
  display: block;
  height: 100%;
  background: var(--ar-primary);
  transition: width 0.3s;
}
.hint {
  margin: 0 0 10px;
  font-size: 12px;
}
</style>
