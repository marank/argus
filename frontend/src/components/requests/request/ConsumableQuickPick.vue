<script setup lang="ts">
import { PackageCheck } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'

import CatalogOptionRow from './CatalogOptionRow.vue'
import { fittingDevices, optionCounts, optionKey } from './types'

/**
 * The catalog's virtual group "For your devices": what fits the employee's own devices,
 * e.g. the ink cartridges for their printer, listed per device like any other group.
 */
const props = defineProps<{
  groups: Schemas['MyConsumablesOut'][]
  catalog: Schemas['CatalogCategoryOut'][]
  cartCounts: Record<string, number>
}>()
const emit = defineEmits<{
  add: [category: Schemas['CatalogCategoryOut'], model: Schemas['CatalogModelOut']]
  remove: [category: Schemas['CatalogCategoryOut'], model: Schemas['CatalogModelOut']]
}>()
const { t } = useI18n()

const devices = computed(() => fittingDevices(props.groups, props.catalog))
</script>

<template>
  <div class="options">
    <header>
      <span class="icon"><PackageCheck :size="22" :stroke-width="1.5" /></span>
      <div>
        <h2>{{ t('requests.new.quickPick') }}</h2>
        <p class="muted">{{ t('requests.new.quickPickHint') }}</p>
      </div>
    </header>

    <section v-for="device in devices" :key="device.asset.id" class="group">
      <div class="eyebrow">
        {{ device.asset.model.full_name }}
        <span class="mono">{{ device.asset.inventory_number }}</span>
      </div>
      <div class="models">
        <CatalogOptionRow
          v-for="option in device.options"
          :key="option.model.id"
          :label="option.model.full_name"
          :counts="optionCounts(option.category, option.model)"
          :in-cart="cartCounts[optionKey(option.category, option.model)] ?? 0"
          @add="emit('add', option.category, option.model)"
          @remove="emit('remove', option.category, option.model)"
        />
      </div>
    </section>
  </div>
</template>

<style scoped>
/* Like a group of the catalog (CategoryOptions). */
.options {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 18px;
  padding: 18px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 3px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
header p {
  margin: 2px 0 0;
}
.group {
  display: grid;
  gap: 8px;
}
.group + .group {
  padding-top: 16px;
  border-top: 1px solid var(--ar-border);
}
.eyebrow .mono {
  margin-left: 6px;
  text-transform: none;
}
.models {
  border: 1px solid var(--ar-border);
  border-radius: 3px;
}
@container catalog (max-width: 480px) {
  .options {
    gap: 14px;
    padding: 12px;
  }
}
</style>
