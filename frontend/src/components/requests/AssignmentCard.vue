<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import AssignmentFields from '@/components/common/AssignmentFields.vue'
import type { Id } from '@/types/common'
import type { AssetRequest } from '@/types/requests'

/** Who is responsible for a request: a team, a person, both or neither. */
const props = defineProps<{ assetRequest: AssetRequest }>()
const emit = defineEmits<{ updated: [assetRequest: AssetRequest] }>()
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
      @updated="(r: AssetRequest) => emit('updated', r)"
    />
  </NCard>
</template>
