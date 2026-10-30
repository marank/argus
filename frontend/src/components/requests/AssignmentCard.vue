<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import AssignmentFields from '@/components/common/AssignmentFields.vue'
import type { Id } from '@/types/common'

/** Who is responsible for a request: a team, a person, both or neither. */
const props = defineProps<{ assetRequest: Schemas['AssetRequestOut'] }>()
const emit = defineEmits<{ updated: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()

const assign = (data: { team: Id | null; assignee: Id | null }) =>
  requestsApi.assign(props.assetRequest.id, data)
</script>

<template>
  <NCard :title="t('common.assignment.title')" size="small">
    <AssignmentFields
      :team="assetRequest.assigned_team"
      :assignee="assetRequest.assignee"
      :assign="assign"
      @updated="(r: Schemas['AssetRequestOut']) => emit('updated', r)"
    />
  </NCard>
</template>
