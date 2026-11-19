<script setup lang="ts">
import { NButton, NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import AssignmentFields from '@/components/common/AssignmentFields.vue'
import { useAssignment } from '@/composables/useAssignment'

/** Who is responsible for a request: a team, a person, both or neither. */
const props = defineProps<{ assetRequest: Schemas['AssetRequestOut'] }>()
const emit = defineEmits<{ updated: [assetRequest: Schemas['AssetRequestOut']] }>()
const { t } = useI18n()

const form = useAssignment(
  () => ({ team: props.assetRequest.assigned_team, assignee: props.assetRequest.assignee }),
  (data) => requestsApi.assign(props.assetRequest.id, data),
  (r) => emit('updated', r),
)
</script>

<template>
  <NCard :title="t('common.assignment.title')" size="small">
    <template #header-extra>
      <NButton
        size="small"
        type="primary"
        :disabled="!form.dirty"
        :loading="form.busy"
        @click="form.save"
      >
        {{ t('common.save') }}
      </NButton>
    </template>
    <AssignmentFields
      :team="assetRequest.assigned_team"
      :assignee="assetRequest.assignee"
      :form="form"
    />
  </NCard>
</template>
