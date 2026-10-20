<script setup lang="ts">
import { NCard, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import { useLive } from '@/composables/useLive'
import { useFeaturesStore } from '@/stores/features'
import type { TeamLoad, WidgetProps } from '@/types/dashboard'

defineProps<WidgetProps>()

/** More rows would push the widget out of shape; the rest is summed up below. */
const MAX_ROWS = 8

const { t } = useI18n()
const features = useFeaturesStore()
const load = ref<TeamLoad | null>(null)

const fetchLoad = async () => (load.value = await dashboardApi.teamLoad())
onMounted(fetchLoad)
useLive(['reservation', 'issue'], fetchLoad)

const withIssues = computed(() => features.isOn('issues'))
const rows = computed(() =>
  (load.value?.people ?? []).map((p) => ({
    ...p,
    total: p.requests + (withIssues.value ? p.issues : 0),
  })),
)
const max = computed(() => Math.max(1, ...rows.value.map((r) => r.total)))
const shown = computed(() => rows.value.slice(0, MAX_ROWS))
const unassigned = computed(
  () =>
    (load.value?.unassigned_requests ?? 0) +
    (withIssues.value ? (load.value?.unassigned_issues ?? 0) : 0),
)

const breakdown = (r: { requests: number; issues: number }) =>
  withIssues.value
    ? t('dashboard.widgets.teamLoad.breakdown', { requests: r.requests, issues: r.issues })
    : t('dashboard.widgets.teamLoad.requestsOnly', { requests: r.requests })
</script>

<template>
  <NCard :title="t('dashboard.widgets.teamLoad.title')" size="small">
    <NSkeleton v-if="!load" text :repeat="4" />
    <template v-else>
      <div class="rows">
        <div v-for="r in shown" :key="r.user.id" class="row" :title="breakdown(r)">
          <span class="name">{{ r.user.display_name }}</span>
          <span class="track">
            <span v-if="r.total" class="bar" :style="{ width: `${(r.total / max) * 100}%` }" />
          </span>
          <span class="mono value">{{ r.total }}</span>
          <small class="muted detail">{{ breakdown(r) }}</small>
        </div>
      </div>
      <p v-if="rows.length > MAX_ROWS" class="muted more">
        {{ t('dashboard.widgets.teamLoad.more', { count: rows.length - MAX_ROWS }) }}
      </p>
      <RouterLink
        :to="{ name: 'reservations', query: { assigned: 'nobody' } }"
        class="unassigned"
        :class="{ warn: unassigned }"
      >
        {{ t('dashboard.widgets.teamLoad.unassigned') }}
        <span class="mono">{{ unassigned }}</span>
      </RouterLink>
    </template>
  </NCard>
</template>

<style scoped>
.rows {
  display: grid;
  grid-template-columns: minmax(0, max-content) minmax(60px, 1fr) auto auto;
  align-items: center;
  gap: 8px 10px;
}
.row {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: subgrid;
  align-items: center;
}
.name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.track {
  display: flex;
  height: 10px;
}
/* Grows from the left baseline: square there, rounded at the data end. */
.bar {
  min-width: 4px;
  border-radius: 0 4px 4px 0;
  background: var(--ar-series-1);
}
.value {
  min-width: 2ch;
  text-align: right;
}
.detail {
  white-space: nowrap;
}
.more {
  margin: 8px 0 0;
  font-size: 12px;
}
.unassigned {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
  padding-top: 8px;
  border-top: 1px solid var(--ar-border);
  color: var(--ar-text-subtle);
  text-decoration: none;
}
.unassigned.warn {
  color: var(--ar-text);
}
.unassigned:hover {
  color: var(--ar-primary);
}
@container (max-width: 420px) {
  .detail {
    display: none;
  }
}
</style>
