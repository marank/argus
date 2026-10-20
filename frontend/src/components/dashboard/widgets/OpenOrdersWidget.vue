<script setup lang="ts">
import { NCard, NSkeleton } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import StatusTag from '@/components/common/StatusTag.vue'
import { toIsoDate } from '@/composables/useFormat'
import type { OpenOrder, WidgetProps } from '@/types/dashboard'

import { useDateMode } from './dateMode'
import DateModeToggle from './DateModeToggle.vue'

/** Placed orders not fully received, by expected delivery; late ones in red. */
const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const { t } = useI18n()
const { mode, setMode, when, other } = useDateMode(
  () => props.options,
  (options) => emit('update:options', options),
)
const orders = ref<OpenOrder[] | null>(null)
onMounted(async () => (orders.value = await dashboardApi.openOrders()))

const late = (order: OpenOrder) =>
  !!order.expected_date && order.expected_date < toIsoDate(Date.now())!
</script>

<template>
  <NCard :title="t('dashboard.widgets.openOrders.title')" size="small">
    <template #header-extra>
      <DateModeToggle :model-value="mode" @update:model-value="setMode" />
    </template>
    <NSkeleton v-if="!orders" text :repeat="3" />
    <p v-else-if="!orders.length" class="muted">{{ t('dashboard.widgets.openOrders.empty') }}</p>
    <div v-else class="lines dated">
      <RouterLink
        v-for="o in orders"
        :key="o.id"
        :to="{ name: 'order', params: { id: o.id } }"
        class="line"
      >
        <span class="mono">{{ o.number }}</span>
        <span class="title">{{ o.supplier?.name ?? '—' }}</span>
        <span
          v-if="o.expected_date"
          class="when"
          :class="{ 'mono muted full': mode === 'full', late: late(o) }"
          :title="other(o.expected_date)"
          >{{ when(o.expected_date) }}</span
        >
        <span v-else class="when muted">{{ t('dashboard.widgets.openOrders.noDate') }}</span>
        <StatusTag group="orderStatus" :value="o.status" />
      </RouterLink>
    </div>
  </NCard>
</template>

<style scoped src="./lines.css"></style>
<style scoped>
.when.late {
  color: var(--ar-error);
}
</style>
