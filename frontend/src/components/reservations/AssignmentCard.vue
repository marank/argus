<script setup lang="ts">
import { UserRoundPlus } from '@lucide/vue'
import { NButton, NCard, NForm, NFormItemGi, NGrid } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { teamsApi, usersApi } from '@/api/accounts'
import { reservationsApi } from '@/api/reservations'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'
import { useAuthStore } from '@/stores/auth'
import type { Id } from '@/types/common'
import type { Team, User } from '@/types/accounts'
import type { Reservation } from '@/types/reservations'

/** Who is responsible for a request: a team, a person, both or neither. Saved on change. */
const props = defineProps<{ reservation: Reservation }>()
const emit = defineEmits<{ updated: [reservation: Reservation] }>()
const { t } = useI18n()
const auth = useAuthStore()
const { busy, run } = useAction()

const team = ref<Id | null>(props.reservation.assigned_team?.id ?? null)
const assignee = ref<Id | null>(props.reservation.assignee?.id ?? null)
/** Members of the chosen team, listed first when picking a person. */
const memberIds = ref(new Set<Id>())

async function loadMembers(id: Id | null) {
  memberIds.value = new Set(id ? (await teamsApi.get(id)).members.map((m) => m.id) : [])
}
onMounted(() => loadMembers(team.value))

// Refs carry what the select labels need (name / display_name).
const initialTeam = computed(() => props.reservation.assigned_team as Team | null)
const initialAssignee = computed(() => props.reservation.assignee as User | null)

const isMine = computed(() => assignee.value === auth.user?.id)

async function save() {
  const updated = await run(
    () =>
      reservationsApi.assign(props.reservation.id, {
        team: team.value,
        assignee: assignee.value,
      }),
    t('common.saved'),
  )
  if (updated) emit('updated', updated)
  else {
    team.value = props.reservation.assigned_team?.id ?? null
    assignee.value = props.reservation.assignee?.id ?? null
  }
}

function onTeam(selected: Team | null) {
  memberIds.value = new Set(selected?.members.map((m) => m.id) ?? [])
  save()
}

function assignToMe() {
  assignee.value = auth.user!.id
  save()
}
</script>

<template>
  <NCard :title="t('reservations.assignment.title')" size="small">
    <template #header-extra>
      <NButton v-if="!isMine" size="tiny" quaternary :loading="busy" @click="assignToMe">
        <template #icon><UserRoundPlus :size="14" /></template>
        {{ t('reservations.assignment.assignToMe') }}
      </NButton>
    </template>
    <NForm label-placement="top" size="small" :show-feedback="false">
      <NGrid :cols="2" :x-gap="12" :y-gap="8" item-responsive responsive="self">
        <NFormItemGi span="2 400:1" :label="t('reservations.assignment.team')">
          <EntitySelect
            v-model="team"
            :fetcher="teamsApi.list"
            :label="(item: Team) => item.name"
            :initial="initialTeam"
            :placeholder="t('reservations.assignment.noTeam')"
            :disabled="busy"
            @select="onTeam"
          />
        </NFormItemGi>
        <NFormItemGi span="2 400:1" :label="t('reservations.assignment.assignee')">
          <EntitySelect
            v-model="assignee"
            :fetcher="usersApi.list"
            :params="{ is_staff: true, is_active: true }"
            :label="(item: User) => item.display_name"
            :initial="initialAssignee"
            :prefer="(item: User) => memberIds.has(item.id)"
            :placeholder="t('reservations.assignment.nobody')"
            :disabled="busy"
            @select="save"
          />
        </NFormItemGi>
      </NGrid>
    </NForm>
  </NCard>
</template>
