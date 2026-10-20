<script setup lang="ts">
import { NCard, NSkeleton } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import type { WaitingRequest, WidgetProps } from '@/types/dashboard'

import { useDateMode } from './dateMode'
import DateModeToggle from './DateModeToggle.vue'

/** Requests waiting for approval, the longest waiting first, with who has them. */
const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const { t } = useI18n()
const { mode, setMode, when, other } = useDateMode(
  () => props.options,
  (options) => emit('update:options', options),
)
const rows = ref<WaitingRequest[] | null>(null)
onMounted(async () => (rows.value = await dashboardApi.waitingRequests()))
</script>

<template>
  <NCard :title="t('dashboard.widgets.waiting.title')" size="small">
    <template #header-extra>
      <DateModeToggle :model-value="mode" @update:model-value="setMode" />
    </template>
    <NSkeleton v-if="!rows" text :repeat="3" />
    <p v-else-if="!rows.length" class="muted">{{ t('dashboard.widgets.waiting.empty') }}</p>
    <div v-else class="lines dated">
      <RouterLink
        v-for="r in rows"
        :key="r.id"
        :to="{ name: 'reservation', params: { id: r.id } }"
        class="line"
      >
        <span class="mono">{{ r.number }}</span>
        <span class="title"
          >{{ r.title }}<small class="muted"> · {{ r.requester.display_name }}</small></span
        >
        <span
          class="when"
          :class="{ 'mono muted full': mode === 'full' }"
          :title="other(r.created_at)"
          >{{ when(r.created_at) }}</span
        >
        <small class="muted assignee">{{
          r.assignee?.display_name ?? t('dashboard.unassigned')
        }}</small>
      </RouterLink>
    </div>
  </NCard>
</template>

<style scoped src="./lines.css"></style>
<style scoped>
.assignee {
  white-space: nowrap;
}
</style>
