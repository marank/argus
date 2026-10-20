<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import type { WidgetProps } from '@/types/dashboard'

defineProps<WidgetProps>()

const { t } = useI18n()
const { dateWithWeekday, relativeDay } = useFormat()
</script>

<template>
  <NCard :title="t('dashboard.upcoming')" size="small">
    <p v-if="!data.upcoming.length" class="muted">{{ t('dashboard.noUpcoming') }}</p>
    <div v-else class="lines dated">
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
        <span class="when">{{ relativeDay(r.pickup_at ?? r.start_date) }}</span>
        <span class="mono muted date">{{ dateWithWeekday(r.pickup_at ?? r.start_date) }}</span>
        <!-- Pending hand-outs wait for IT: the dot pulses. -->
        <StatusTag group="reservationStatus" :value="r.status" pulse />
      </RouterLink>
    </div>
  </NCard>
</template>

<style scoped src="./lines.css"></style>
