<script setup lang="ts">
import { NCard } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import { reservationsApi } from '@/api/reservations'
import AssignmentFields from '@/components/common/AssignmentFields.vue'
import type { Id } from '@/types/common'
import type { Reservation } from '@/types/reservations'

/** Who is responsible for a request: a team, a person, both or neither. */
const props = defineProps<{ reservation: Reservation }>()
const emit = defineEmits<{ updated: [reservation: Reservation] }>()
const { t } = useI18n()

const assign = (data: { team: Id | null; assignee: Id | null }) =>
  reservationsApi.assign(props.reservation.id, data)
</script>

<template>
  <NCard :title="t('common.assignment.title')" size="small">
    <AssignmentFields
      :team="reservation.assigned_team"
      :assignee="reservation.assignee"
      :assign="assign"
      @updated="(r: Reservation) => emit('updated', r)"
    />
  </NCard>
</template>
