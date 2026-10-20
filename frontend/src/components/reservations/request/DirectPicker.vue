<script setup lang="ts">
import { watchDebounced } from '@vueuse/core'
import { Check, Plus, ScanLine } from '@lucide/vue'
import { NButton, NInput, NSpin, useMessage } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { assetsApi, consumablesApi, lookupApi } from '@/api/inventory'
import EmptyState from '@/components/common/EmptyState.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { useScanner } from '@/composables/useScanner'
import type { Asset, Consumable } from '@/types/inventory'
import type { CatalogCategory } from '@/types/reservations'

/**
 * Middle column of a direct hand-out: scan or search specific devices in stock,
 * or browse what the group chosen on the left has in stock.
 */
const props = defineProps<{
  category: CatalogCategory | null
  /** Keys of the cart lines, to mark what is already picked. */
  cartCounts: Record<string, number>
}>()
const emit = defineEmits<{ addAsset: [asset: Asset]; addConsumable: [consumable: Consumable] }>()
const { t } = useI18n()
const { enumLabel } = useFormat()
const message = useMessage()
const { run } = useAction()

const query = ref('')
const loading = ref(false)
const assets = ref<Asset[]>([])
const consumables = ref<Consumable[]>([])

let latest = 0
async function load() {
  const q = query.value.trim()
  const filter = q ? { q } : props.category ? { category: props.category.id } : null
  const current = ++latest
  if (!filter) {
    assets.value = []
    consumables.value = []
    return
  }
  loading.value = true
  try {
    const [devicePage, stockPage] = await Promise.all([
      assetsApi.list({
        ...filter,
        status: ['in_stock'],
        ordering: 'inventory_number',
        page_size: 50,
      }),
      consumablesApi.list({ ...filter, page_size: 50 }),
    ])
    if (current !== latest) return
    assets.value = devicePage.items
    consumables.value = stockPage.items.filter((c) => c.available_quantity > 0)
  } finally {
    if (current === latest) loading.value = false
  }
}
watch(() => props.category?.id, load, { immediate: true })
watchDebounced(query, load, { debounce: 250 })

const picked = (key: string) => props.cartCounts[key] ?? 0

/** Enter on the field or a scanner anywhere on the page: add the device right away. */
async function scan(code = query.value) {
  const value = code.trim()
  if (!value) return
  const found = await run(() => lookupApi.lookup(value))
  if (!found) return
  const asset =
    found.assets.find((a) => a.status === 'in_stock') ??
    (found.assets.length === 1 ? found.assets[0] : undefined)
  if (!asset) {
    message.warning(t('reservations.direct.notFound', { code: value }))
    return
  }
  if (asset.status !== 'in_stock') {
    message.warning(
      t('reservations.direct.notInStock', {
        number: asset.inventory_number,
        status: enumLabel('assetStatus', asset.status),
      }),
    )
    return
  }
  emit('addAsset', asset)
  query.value = ''
}
useScanner(scan)

const heading = computed(() =>
  query.value.trim()
    ? t('reservations.direct.results')
    : props.category
      ? props.category.name
      : t('reservations.direct.inStock'),
)
const empty = computed(() => !loading.value && !assets.value.length && !consumables.value.length)
</script>

<template>
  <section class="picker">
    <NInput
      v-model:value="query"
      size="large"
      clearable
      autofocus
      class="scan"
      :placeholder="t('reservations.direct.scan')"
      @keydown.enter.prevent="scan()"
    >
      <template #prefix><ScanLine :size="18" /></template>
    </NInput>

    <header>
      <h2>{{ heading }}</h2>
      <span class="muted">{{ t('reservations.direct.inStock') }}</span>
      <NSpin v-if="loading" :size="14" />
    </header>

    <EmptyState
      v-if="empty"
      :text="
        query.trim() || category
          ? t('reservations.direct.noStock')
          : t('reservations.direct.pickHint')
      "
    />

    <ul v-else class="rows">
      <li v-for="asset in assets" :key="asset.id" :class="{ picked: picked(`a${asset.id}`) }">
        <span class="mono code">{{ asset.inventory_number }}</span>
        <span class="text">
          <span class="label">{{ asset.model.full_name }}</span>
          <span class="muted meta">
            {{ [asset.serial_number, asset.location?.name].filter(Boolean).join(' · ') }}
          </span>
        </span>
        <span v-if="picked(`a${asset.id}`)" class="in-cart">
          <Check :size="14" /> {{ t('reservations.direct.picked') }}
        </span>
        <NButton v-else secondary size="small" @click="emit('addAsset', asset)">
          <template #icon><Plus :size="14" /></template>
          {{ t('common.add') }}
        </NButton>
      </li>
      <li v-for="consumable in consumables" :key="consumable.id">
        <span class="mono code">{{ consumable.available_quantity }}×</span>
        <span class="text">
          <span class="label">{{ consumable.model.full_name }}</span>
          <span class="muted meta">
            {{
              t('reservations.allocation.consumableFrom', { location: consumable.location.name })
            }}
          </span>
        </span>
        <span v-if="picked(`s${consumable.id}`)" class="in-cart mono">
          <Check :size="14" /> {{ picked(`s${consumable.id}`) }}
        </span>
        <NButton
          secondary
          size="small"
          :disabled="picked(`s${consumable.id}`) >= consumable.available_quantity"
          @click="emit('addConsumable', consumable)"
        >
          <template #icon><Plus :size="14" /></template>
          {{ t('common.add') }}
        </NButton>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.picker {
  display: grid;
  gap: 12px;
  padding: 18px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
.scan :deep(input) {
  font-family: var(--ar-font-mono);
}
header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-top: 4px;
}
h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
header .muted {
  font-size: 12px;
}
.rows {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}
.rows li {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 9px 0;
  border-bottom: 1px solid var(--ar-border);
}
.rows li:last-child {
  border-bottom: none;
}
.rows li.picked .label,
.rows li.picked .code {
  color: var(--ar-text-muted);
}
.code {
  color: var(--ar-primary);
}
.text {
  display: grid;
  min-width: 0;
}
.label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
}
.meta {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 11.5px;
}
.in-cart {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  color: var(--ar-success);
  font-size: 12px;
}
.rows li:has(.in-cart + .n-button) {
  grid-template-columns: 96px minmax(0, 1fr) auto auto;
}
</style>
