<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import StatusTag from '@/components/common/StatusTag.vue'
import { useFormat } from '@/composables/useFormat'
import type { ITOverview } from '@/types/dashboard'

defineProps<{ data: ITOverview }>()

const { t } = useI18n()
const { date, dateTime } = useFormat()
</script>

<template>
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
</template>

<style scoped src="./lines.css"></style>
