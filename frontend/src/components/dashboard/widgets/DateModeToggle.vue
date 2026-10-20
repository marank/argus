<script setup lang="ts">
import { CalendarDays, History } from '@lucide/vue'
import { NButton } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import type { DateMode } from './dateMode'

/** Switches a widget's dates between "Morgen, 12:00 Uhr" and the full date. */
const mode = defineModel<DateMode>({ required: true })

const { t } = useI18n()
</script>

<template>
  <NButton
    quaternary
    size="tiny"
    :title="
      mode === 'full'
        ? t('dashboard.widgets.dates.showRelative')
        : t('dashboard.widgets.dates.showFull')
    "
    @click="mode = mode === 'full' ? 'relative' : 'full'"
  >
    <template #icon><component :is="mode === 'full' ? History : CalendarDays" /></template>
  </NButton>
</template>
