<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import type { AssetRequest } from '@/types/requests'
import { categoryIcon } from '@/utils/icons'
import { itemLabel } from '@/utils/requests'

/** What was asked for, large and plain: for deciding on a request at a glance. */
defineProps<{ assetRequest: AssetRequest }>()
const { t } = useI18n()
</script>

<template>
  <NCard :title="t('requests.items')" size="small">
    <ul class="items">
      <li v-for="item in assetRequest.items" :key="item.id">
        <span class="icon">
          <component :is="categoryIcon(item.category?.icon)" :size="22" :stroke-width="1.5" />
        </span>
        <span class="text">
          <strong>{{ itemLabel(item) }}</strong>
          <span class="muted meta">
            {{ item.category?.name }}
            <span v-if="item.is_free_text" class="free">{{ t('requests.freeText') }}</span>
          </span>
          <span v-if="item.note" class="note">{{ item.note }}</span>
        </span>
        <span class="quantity mono">{{ item.quantity_requested }}×</span>
      </li>
    </ul>
  </NCard>
</template>

<style scoped>
.items {
  display: grid;
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}
li {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 14px;
  padding: 12px 14px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface-sunken);
}
.icon {
  display: grid;
  place-items: center;
  width: 42px;
  height: 42px;
  border-radius: 3px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
.text {
  display: grid;
  gap: 2px;
  min-width: 0;
}
strong {
  font-size: 15px;
  overflow-wrap: anywhere;
}
.meta {
  font-size: 12px;
}
.free {
  margin-left: 6px;
  color: var(--ar-warning);
  font-weight: 600;
}
.note {
  font-size: 12.5px;
}
.quantity {
  font-size: 20px;
  font-weight: 600;
}
</style>
