<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'
import { RouterLink } from 'vue-router'

import { useActivity } from '@/composables/useActivity'
import { activityTarget } from '@/types/activity'
import type { WidgetProps } from '@/types/dashboard'

import { useDateMode } from './dateMode'
import DateModeToggle from './DateModeToggle.vue'

const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const { t } = useI18n()
const { summary } = useActivity()
// Activity has always shown full dates; that stays the default.
const { mode, setMode, when, other } = useDateMode(
  () => props.options,
  (options) => emit('update:options', options),
  'full',
)
</script>

<template>
  <NCard :title="t('dashboard.recentActivity')" size="small">
    <template #header-extra>
      <span class="extra">
        <RouterLink :to="{ name: 'activities' }" class="muted">{{
          t('activity.showAll')
        }}</RouterLink>
        <DateModeToggle :model-value="mode" @update:model-value="setMode" />
      </span>
    </template>
    <div class="lines activity">
      <component
        :is="activityTarget(e) ? RouterLink : 'div'"
        v-for="e in data.recent_events"
        :key="e.id"
        :to="activityTarget(e) ?? undefined"
        class="line"
      >
        <span class="title"
          >{{ summary(e) }}<small class="muted"> · {{ e.subject_label }}</small></span
        >
        <span class="muted actor">{{ e.actor?.display_name ?? '' }}</span>
        <span
          class="when"
          :class="{ 'mono muted full': mode === 'full' }"
          :title="other(e.occurred_at)"
          >{{ when(e.occurred_at) }}</span
        >
      </component>
    </div>
  </NCard>
</template>

<style scoped src="./lines.css"></style>
<style scoped>
/* Object and step first, then who and when. */
.lines.activity {
  grid-template-columns: minmax(0, 1fr) auto auto;
}
.extra {
  display: inline-flex;
  align-items: center;
  gap: 12px;
}
.actor {
  white-space: nowrap;
}
</style>
