<script setup lang="ts">
import { Check, Plus } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Id } from '@/types/common'
import type { CatalogCategory, CatalogModel, MyConsumables } from '@/types/requests'

import { optionKey } from './types'

/**
 * Quick pick of consumables that fit the employee's own devices, e.g. the ink
 * cartridges for their printer. Only consumables listed in the catalog are offered.
 */
const props = defineProps<{
  groups: MyConsumables[]
  catalog: CatalogCategory[]
  cartCounts: Record<string, number>
}>()
const emit = defineEmits<{ add: [category: CatalogCategory, model: CatalogModel] }>()
const { t } = useI18n()

const catalogModels = computed(() => {
  const byId = new Map<Id, { category: CatalogCategory; model: CatalogModel }>()
  for (const category of props.catalog) {
    for (const model of category.models) byId.set(model.id, { category, model })
  }
  return byId
})

const devices = computed(() =>
  props.groups
    .map((group) => ({
      asset: group.asset,
      options: group.consumables.flatMap((c) => catalogModels.value.get(c.id) ?? []),
    }))
    .filter((device) => device.options.length),
)
</script>

<template>
  <section v-if="devices.length" class="quick-pick">
    <div class="eyebrow">{{ t('requests.new.quickPick') }}</div>
    <div v-for="device in devices" :key="device.asset.id" class="device">
      <div class="device-name">
        {{ device.asset.model.full_name }}
        <span class="mono muted">{{ device.asset.inventory_number }}</span>
      </div>
      <div class="chips">
        <button
          v-for="option in device.options"
          :key="option.model.id"
          type="button"
          class="chip"
          :class="{ added: cartCounts[optionKey(option.category, option.model)] }"
          :title="t('requests.new.quickPickAdd', { name: option.model.full_name })"
          @click="emit('add', option.category, option.model)"
        >
          <Plus :size="13" />
          <span>{{ option.model.full_name }}</span>
          <span
            v-if="cartCounts[optionKey(option.category, option.model)]"
            :key="cartCounts[optionKey(option.category, option.model)]"
            class="count mono"
          >
            <Check :size="12" />{{ cartCounts[optionKey(option.category, option.model)] }}
          </span>
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.quick-pick {
  display: grid;
  gap: 10px;
  padding: 12px 14px;
  border: 1px solid color-mix(in srgb, var(--ar-primary) 35%, transparent);
  border-radius: 3px;
  background: var(--ar-primary-soft);
}
.device {
  display: grid;
  gap: 6px;
}
.device-name {
  font-size: 12.5px;
  font-weight: 600;
}
.device-name .mono {
  margin-left: 6px;
  font-size: 11px;
  font-weight: 400;
}
.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}
.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border: 1px solid var(--ar-border-strong);
  border-radius: 999px;
  background: var(--ar-surface);
  color: var(--ar-text);
  font: inherit;
  font-size: 12.5px;
  cursor: pointer;
}
.chip:hover {
  border-color: var(--ar-primary);
  color: var(--ar-primary);
}
.chip.added {
  border-color: var(--ar-primary);
}
.count {
  /* Re-keyed on every change, so the pop plays when something is added. */
  animation: ar-pop 0.25s ease-out;
  display: inline-flex;
  align-items: center;
  gap: 2px;
  font-size: 11px;
  color: var(--ar-primary);
}
</style>
