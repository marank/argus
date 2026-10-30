<script setup lang="ts">
import { NCard, NSkeleton } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import { useLive } from '@/composables/useLive'
import { useFeaturesStore } from '@/stores/features'
import type { Schemas } from '@/api/types'
import type { WidgetProps } from '@/types/dashboard'

import { useDateMode } from './dateMode'
import DateModeToggle from './DateModeToggle.vue'

const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const { t } = useI18n()
const { enumLabel } = useFormat()
const { mode, setMode, when, other } = useDateMode(
  () => props.options,
  (options) => emit('update:options', options),
)
const features = useFeaturesStore()
const tasks = ref<Schemas['MyTasksOut'] | null>(null)

const load = async () => (tasks.value = await dashboardApi.myTasks())
onMounted(load)
useLive(['request', 'issue'], load)
</script>

<template>
  <NCard :title="t('dashboard.widgets.myTasks.title')" size="small">
    <template #header-extra>
      <DateModeToggle :model-value="mode" @update:model-value="setMode" />
    </template>
    <NSkeleton v-if="!tasks" text :repeat="3" />
    <p v-else-if="!tasks.requests_total && !tasks.issues_total" class="muted">
      {{ t('dashboard.widgets.myTasks.empty') }}
    </p>
    <div v-else class="lines dated">
      <template v-if="tasks.requests_total">
        <RouterLink :to="{ name: 'requests', query: { assigned: 'me' } }" class="section eyebrow">
          {{ t('dashboard.widgets.myTasks.requests', { count: tasks.requests_total }) }}
        </RouterLink>
        <RouterLink
          v-for="r in tasks.requests"
          :key="r.id"
          :to="{ name: 'request', params: { id: r.id } }"
          class="line"
        >
          <span class="mono">{{ r.number }}</span>
          <span class="title"
            >{{ r.title }}<small class="muted"> · {{ r.requester.display_name }}</small></span
          >
          <span
            class="when"
            :class="{ 'mono muted full': mode === 'full' }"
            :title="other(r.start_date)"
            >{{ when(r.start_date) }}</span
          >
          <StatusTag group="requestStatus" :value="r.status" />
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
          <span
            class="when"
            :class="{ 'mono muted full': mode === 'full' }"
            :title="other(i.created_at.slice(0, 10))"
            >{{ when(i.created_at.slice(0, 10)) }}</span
          >
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
