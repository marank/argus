<script setup lang="ts">
import { NCard } from 'naive-ui'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import type { ITOverview } from '@/types/dashboard'
import { ASSET_STATUSES } from '@/types/inventory'
import { toneOf } from '@/utils/status'

const props = defineProps<{ data: ITOverview }>()

const { t } = useI18n()
const { enumLabel } = useFormat()

const totalAssets = computed(() =>
  Object.values(props.data.asset_status).reduce((sum, n) => sum + n, 0),
)
const statusBars = computed(() =>
  ASSET_STATUSES.map((status) => {
    const count = props.data.asset_status[status] ?? 0
    return { status, count, share: totalAssets.value ? (count / totalAssets.value) * 100 : 0 }
  }),
)
</script>

<template>
  <NCard :title="t('dashboard.devicesByStatus')" size="small">
    <template #header-extra
      ><span class="mono muted">Σ {{ totalAssets }}</span></template
    >
    <div class="bar">
      <RouterLink
        v-for="bar in statusBars.filter((b) => b.count)"
        :key="bar.status"
        :to="{ name: 'assets', query: { status: bar.status } }"
        :style="{ width: `${bar.share}%` }"
        :data-tone="toneOf('assetStatus', bar.status)"
        :title="`${enumLabel('assetStatus', bar.status)}: ${bar.count}`"
      />
    </div>
    <div class="legend">
      <RouterLink
        v-for="bar in statusBars"
        :key="bar.status"
        :to="{ name: 'assets', query: { status: bar.status } }"
        class="legend-item"
      >
        <StatusTag group="assetStatus" :value="bar.status" />
        <span class="mono">{{ bar.count }}</span>
      </RouterLink>
    </div>
  </NCard>
</template>

<style scoped>
.bar {
  display: flex;
  height: 10px;
  gap: 2px;
  border-radius: 2px;
  overflow: hidden;
  background: var(--ar-surface-sunken);
}
.bar a {
  --tone: var(--ar-text-subtle);
  background: var(--tone);
}
.bar a[data-tone='info'] {
  --tone: var(--ar-info);
}
.bar a[data-tone='success'] {
  --tone: var(--ar-success);
}
.bar a[data-tone='warning'] {
  --tone: var(--ar-warning);
}
.bar a[data-tone='error'] {
  --tone: var(--ar-error);
}
.bar a[data-tone='primary'] {
  --tone: var(--ar-primary);
}
.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 12px;
}
/* Links to the filtered device list: highlighted as a chip instead of underlined. */
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin: -3px -6px;
  padding: 3px 6px;
  border-radius: 3px;
  color: inherit;
  text-decoration: none;
  transition: background-color 0.15s ease;
}
.legend-item:hover,
.legend-item:focus-visible {
  background: var(--ar-surface-sunken);
  text-decoration: none;
}
.legend-item:hover .status-tag,
.legend-item:focus-visible .status-tag {
  background: color-mix(in srgb, var(--tone) 18%, transparent);
  border-color: var(--tone);
}
</style>
