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
        :label="t('dashboard.lowStock')"
        :value="data.low_stock"
        :icon="CircleAlert"
        :tone="data.low_stock ? 'warning' : 'default'"
        :to="{ name: 'stock', query: { below_minimum: '1' } }"
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
          <StatusTag group="reservationStatus" :value="r.status" />
        </RouterLink>
      </NCard>
      <NCard :title="t('dashboard.recentActivity')" size="small">
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
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: inherit;
}
.line {
  display: grid;
  grid-template-columns: 112px 1fr auto auto;
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
