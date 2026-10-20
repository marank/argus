<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { useFormat } from '@/composables/useFormat'
import type { ITOverview } from '@/types/dashboard'

defineProps<{ data: ITOverview }>()

const { t } = useI18n()
const { dateTime, enumLabel } = useFormat()
</script>

<template>
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
</template>

<style scoped src="./lines.css"></style>
