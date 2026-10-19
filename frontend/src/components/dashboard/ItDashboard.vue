<script setup lang="ts">
import {
  AlarmClock,
  CircleAlert,
  ClipboardCheck,
  PackageCheck,
  PackageOpen,
  ShieldAlert,
  ShoppingCart,
  Truck,
} from '@lucide/vue'
import { NCard, NSkeleton } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import StatCard from '@/components/common/StatCard.vue'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import { ASSET_STATUSES } from '@/types/inventory'
import type { ITOverview } from '@/types/dashboard'
import { toneOf } from '@/utils/status'

const { t } = useI18n()
const { date, dateTime, enumLabel } = useFormat()
const data = ref<ITOverview | null>(null)

onMounted(async () => (data.value = await dashboardApi.it()))

const totalAssets = computed(() =>
  Object.values(data.value?.asset_status ?? {}).reduce((sum, n) => sum + n, 0),
)
const statusBars = computed(() =>
  ASSET_STATUSES.map((status) => ({
    status,
    count: data.value?.asset_status[status] ?? 0,
    share: totalAssets.value
      ? ((data.value?.asset_status[status] ?? 0) / totalAssets.value) * 100
      : 0,
  })),
)
</script>

<template>
  <div v-if="!data" class="stack">
    <NSkeleton height="90px" :repeat="2" />
  </div>
  <div v-else class="stack">
    <section class="stats">
      <StatCard
        :label="t('dashboard.toApprove')"
        :value="data.reservations_submitted"
        :icon="ClipboardCheck"
        tone="warning"
        :alert="!!data.reservations_submitted"
        :to="{ name: 'reservations', query: { status: 'submitted' } }"
      />
      <StatCard
        :label="t('dashboard.toPrepare')"
        :value="data.reservations_to_prepare"
        :icon="PackageOpen"
        tone="primary"
        :to="{ name: 'reservations', query: { status: 'approved' } }"
      />
      <StatCard
        :label="t('dashboard.readyForPickup')"
        :value="data.reservations_ready"
        :icon="PackageCheck"
        tone="success"
        :to="{ name: 'reservations', query: { status: 'ready' } }"
      />
      <StatCard
        :label="t('dashboard.overdue')"
        :value="data.reservations_overdue"
        :icon="AlarmClock"
        :tone="data.reservations_overdue ? 'error' : 'default'"
        :alert="!!data.reservations_overdue"
        :to="{ name: 'reservations', query: { overdue: '1' } }"
      />
      <StatCard
        :label="t('dashboard.ordersToPlace')"
        :value="data.orders_to_place"
        :icon="ShoppingCart"
        :to="{ name: 'orders', query: { status: 'draft' } }"
      />
      <StatCard
        :label="t('dashboard.ordersInTransit')"
        :value="data.orders_in_transit"
        :icon="Truck"
        tone="info"
        :to="{ name: 'orders', query: { status: 'ordered' } }"
      />
      <StatCard
        :label="t('dashboard.belowMinimum')"
        :value="data.low_consumables"
        :icon="CircleAlert"
        :tone="data.low_consumables ? 'warning' : 'default'"
        :alert="!!data.low_consumables"
        :to="{ name: 'consumables', query: { below_minimum: '1' } }"
      />
      <StatCard
        :label="t('dashboard.warrantyExpiring')"
        :value="data.warranty_expiring"
        :icon="ShieldAlert"
      />
    </section>

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

    <div class="grid-2">
      <NCard :title="t('dashboard.upcoming')" size="small">
        <p v-if="!data.upcoming.length" class="muted">{{ t('dashboard.noUpcoming') }}</p>
        <div v-else class="lines upcoming">
          <RouterLink
            v-for="r in data.upcoming"
            :key="r.id"
            :to="{ name: 'reservation', params: { id: r.id } }"
            class="line"
          >
            <span class="mono">{{ r.number }}</span>
            <span class="title"
              >{{ r.title }}<small class="muted"> · {{ r.requester.display_name }}</small></span
            >
            <span class="mono muted">{{
              r.pickup_at ? dateTime(r.pickup_at) : date(r.start_date)
            }}</span>
            <!-- Pending hand-outs wait for IT: the dot pulses. -->
            <StatusTag group="reservationStatus" :value="r.status" pulse />
          </RouterLink>
        </div>
      </NCard>
      <NCard :title="t('dashboard.recentActivity')" size="small">
        <div class="lines activity">
          <RouterLink
            v-for="e in data.recent_events"
            :key="e.id"
            :to="{ name: 'asset', params: { id: e.asset.id } }"
            class="line"
          >
            <span class="mono">{{ e.asset.inventory_number }}</span>
            <span class="title"
              >{{ enumLabel('eventKind', e.kind)
              }}<small class="muted"> · {{ e.asset.model.full_name }}</small></span
            >
            <span class="mono muted">{{ dateTime(e.occurred_at) }}</span>
          </RouterLink>
        </div>
      </NCard>
    </div>
  </div>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(190px, 1fr));
  gap: 10px;
}
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
/* Lines share one grid (subgrid), so numbers, dates and statuses line up. */
.lines {
  display: grid;
  column-gap: 12px;
}
.lines.upcoming {
  grid-template-columns: auto minmax(0, 1fr) auto auto;
}
.lines.activity {
  grid-template-columns: auto minmax(0, 1fr) auto;
}
.line {
  display: grid;
  grid-column: 1 / -1;
  grid-template-columns: subgrid;
  align-items: center;
  gap: 12px;
  padding: 7px 0;
  border-bottom: 1px solid var(--ar-border);
  color: inherit;
  text-decoration: none;
}
.line:last-child {
  border-bottom: none;
}
.line:hover .title {
  color: var(--ar-primary);
}
.title {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
