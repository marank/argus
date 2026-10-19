<script setup lang="ts">
import { NRadioButton, NRadioGroup } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import type { Assigned } from '@/composables/useAssigned'

const model = defineModel<Assigned>({ required: true })
const { t } = useI18n()
</script>

<template>
  <NRadioGroup v-model:value="model" size="small">
    <NRadioButton value="me">{{ t('common.assignment.me') }}</NRadioButton>
    <NRadioButton value="my_teams">{{ t('common.assignment.myTeams') }}</NRadioButton>
    <NRadioButton value="nobody">{{ t('common.assignment.unassigned') }}</NRadioButton>
    <NRadioButton value="all">{{ t('common.assignment.allAssignments') }}</NRadioButton>
  </NRadioGroup>
</template>
