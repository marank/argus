<script setup lang="ts">
import { NCard, NSkeleton } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import { useFeaturesStore } from '@/stores/features'
import type { MyTasks, WidgetProps } from '@/types/dashboard'

defineProps<WidgetProps>()

const { t } = useI18n()
const { dateWithWeekday, enumLabel, relativeDay } = useFormat()
const features = useFeaturesStore()
const tasks = ref<MyTasks | null>(null)

onMounted(async () => (tasks.value = await dashboardApi.myTasks()))
</script>

<template>
  <NCard :title="t('dashboard.widgets.myTasks.title')" size="small">
    <NSkeleton v-if="!tasks" text :repeat="3" />
    <p v-else-if="!tasks.requests_total && !tasks.issues_total" class="muted">
      {{ t('dashboard.widgets.myTasks.empty') }}
    </p>
    <div v-else class="lines dated">
      <template v-if="tasks.requests_total">
        <RouterLink
          :to="{ name: 'reservations', query: { assigned: 'me' } }"
          class="section eyebrow"
        >
          {{ t('dashboard.widgets.myTasks.requests', { count: tasks.requests_total }) }}
        </RouterLink>
        <RouterLink
          v-for="r in tasks.requests"
          :key="r.id"
          :to="{ name: 'reservation', params: { id: r.id } }"
          class="line"
        >
          <span class="mono">{{ r.number }}</span>
          <span class="title"
            >{{ r.title }}<small class="muted"> · {{ r.requester.display_name }}</small></span
          >
          <span class="when">{{ relativeDay(r.start_date) }}</span>
          <span class="mono muted date">{{ dateWithWeekday(r.start_date) }}</span>
          <StatusTag group="reservationStatus" :value="r.status" />
        </RouterLink>
      </template>
      <template v-if="features.isOn('issues') && tasks.issues_total">
        <RouterLink :to="{ name: 'issues', query: { assigned: 'me' } }" class="section eyebrow">
          {{ t('dashboard.widgets.myTasks.issues', { count: tasks.issues_total }) }}
        </RouterLink>
        <RouterLink
          v-for="i in tasks.issues"
          :key="i.id"
          :to="{ name: 'asset', params: { id: i.asset.id } }"
          class="line"
          :title="i.description"
        >
          <span class="mono">{{ i.asset.inventory_number }}</span>
          <span class="title"
            >{{ enumLabel('issueKind', i.kind)
            }}<small class="muted"> · {{ i.asset.model.full_name }}</small></span
          >
          <span class="when">{{ relativeDay(i.created_at.slice(0, 10)) }}</span>
          <span class="mono muted date">{{ dateWithWeekday(i.created_at.slice(0, 10)) }}</span>
          <StatusTag group="issueStatus" :value="i.status" />
        </RouterLink>
      </template>
    </div>
  </NCard>
</template>

<style scoped src="./lines.css"></style>
<style scoped>
a.section {
  display: block;
  text-decoration: none;
}
a.section:hover {
  color: var(--ar-primary);
}
</style>
