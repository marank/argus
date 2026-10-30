<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { ClipboardList, PackageCheck, PackagePlus, UserRound } from '@lucide/vue'
import { NButton, NCard } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import StatCard from '@/components/common/StatCard.vue'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import { isPast } from '@/utils/requests'

const { t } = useI18n()
const { weekday } = useFormat()
const data = ref<Schemas['EmployeeOverviewOut'] | null>(null)

const load = async () => (data.value = await dashboardApi.me())
onMounted(load)
useLive(['request', 'issue', 'asset', 'license'], load)
</script>

<template>
  <div v-if="data" class="stack">
    <section class="stats">
      <StatCard
        :label="t('dashboard.openRequests')"
        :value="data.open_requests"
        :icon="ClipboardList"
        tone="primary"
        :to="{ name: 'portal-requests' }"
      />
      <StatCard
        :label="t('dashboard.pickupReady')"
        :value="data.ready_for_pickup.length"
        :icon="PackageCheck"
        :tone="data.ready_for_pickup.length ? 'success' : 'default'"
        :to="{ name: 'portal-requests' }"
      />
      <StatCard
        :label="t('dashboard.assignedDevices')"
        :value="data.assigned_assets"
        :icon="UserRound"
        :to="{ name: 'portal-devices' }"
      />
    </section>

    <NCard
      v-if="data.ready_for_pickup.length"
      :title="t('dashboard.pickupReady')"
      size="small"
      class="ready"
    >
      <RouterLink
        v-for="r in data.ready_for_pickup"
        :key="r.id"
        :to="{ name: 'portal-request', params: { id: r.id } }"
        class="line"
      >
        <span class="mono">{{ r.number }}</span>
        <span>{{ r.title }}</span>
        <strong class="mono" :class="{ passed: isPast(r.pickup_at) }">{{
          isPast(r.pickup_at)
            ? t('dashboard.pickupMissed', { date: weekday(r.pickup_at) })
            : t('dashboard.pickupAt', { date: weekday(r.pickup_at) })
        }}</strong>
      </RouterLink>
    </NCard>

    <!-- Overdue returns first; the card turns red as soon as one is late. -->
    <NCard
      v-if="data.returns_due.length"
      :title="t('dashboard.returnsDue')"
      size="small"
      class="returns"
      :class="{ late: data.returns_due.some((r) => isPast(r.end_date)) }"
    >
      <RouterLink
        v-for="r in data.returns_due"
        :key="r.id"
        :to="{ name: 'portal-request', params: { id: r.id } }"
        class="line"
      >
        <span class="mono">{{ r.number }}</span>
        <span>{{ r.title }}</span>
        <strong class="mono" :class="{ late: isPast(r.end_date) }">{{
          isPast(r.end_date)
            ? t('dashboard.returnOverdue', { date: weekday(r.end_date) })
            : t('dashboard.returnBy', { date: weekday(r.end_date) })
        }}</strong>
      </RouterLink>
    </NCard>

    <RouterLink :to="{ name: 'portal-new' }">
      <NButton type="primary" size="large">
        <template #icon><PackagePlus :size="18" /></template>
        {{ t('dashboard.requestCta') }}
      </NButton>
    </RouterLink>
  </div>
</template>

<style scoped>
.stats {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 10px;
}
.ready {
  border-left: 3px solid var(--ar-success);
}
.line {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 16px;
  padding: 6px 0;
  color: inherit;
}
.line strong {
  margin-left: auto;
  color: var(--ar-success);
}
.line strong.passed {
  color: var(--ar-warning);
}
.returns {
  border-left: 3px solid var(--ar-warning);
}
.returns.late {
  border-left-color: var(--ar-error);
}
.returns .line strong {
  color: var(--ar-warning);
}
.returns .line strong.late {
  color: var(--ar-error);
}
</style>
