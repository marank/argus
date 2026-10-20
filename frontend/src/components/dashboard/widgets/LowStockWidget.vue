<script setup lang="ts">
import { NCard, NSkeleton } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import { useFeaturesStore } from '@/stores/features'
import type { LowStockItem, WidgetProps } from '@/types/dashboard'

/** Consumables below their minimum; they are on the needs list to be ordered. */
defineProps<WidgetProps>()

const { t } = useI18n()
const features = useFeaturesStore()
const items = ref<LowStockItem[] | null>(null)
onMounted(async () => (items.value = await dashboardApi.lowStock()))
</script>

<template>
  <NCard :title="t('dashboard.widgets.lowStock.title')" size="small">
    <template #header-extra>
      <RouterLink v-if="features.isOn('procurement')" :to="{ name: 'needs' }" class="muted">
        {{ t('nav.needs') }}
      </RouterLink>
    </template>
    <NSkeleton v-if="!items" text :repeat="3" />
    <p v-else-if="!items.length" class="muted">{{ t('dashboard.widgets.lowStock.empty') }}</p>
    <div v-else class="lines cols-3">
      <RouterLink
        v-for="item in items"
        :key="item.id"
        :to="{ name: 'consumables', query: { below_minimum: '1' } }"
        class="line"
      >
        <span class="title"
          >{{ item.model.full_name }}<small class="muted"> · {{ item.location.name }}</small></span
        >
        <span
          class="mono stock"
          :class="{ empty: item.quantity <= 0 }"
          :title="t('dashboard.widgets.lowStock.missing', item.min_quantity - item.quantity)"
        >
          {{ item.quantity }}
        </span>
        <span class="mono muted">/ {{ item.min_quantity }}</span>
      </RouterLink>
    </div>
  </NCard>
</template>

<style scoped src="./lines.css"></style>
<style scoped>
.lines.cols-3 {
  grid-template-columns: minmax(0, 1fr) auto auto;
}
.stock {
  color: var(--ar-warning);
  text-align: right;
}
.stock.empty {
  color: var(--ar-error);
}
</style>
