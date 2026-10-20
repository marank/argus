<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { useFormat } from '@/composables/useFormat'
import type { WidgetProps } from '@/types/dashboard'

import { useDateMode } from './dateMode'
import DateModeToggle from './DateModeToggle.vue'

const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const { t } = useI18n()
const { enumLabel } = useFormat()
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
      <DateModeToggle :model-value="mode" @update:model-value="setMode" />
    </template>
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
        <span
          class="when"
          :class="{ 'mono muted full': mode === 'full' }"
          :title="other(e.occurred_at)"
          >{{ when(e.occurred_at) }}</span
        >
      </RouterLink>
    </div>
  </NCard>
</template>

<style scoped src="./lines.css"></style>
