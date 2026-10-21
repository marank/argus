<script setup lang="ts" generic="T">
import { UserRoundPlus } from '@lucide/vue'
import { NButton, NForm, NFormItemGi, NGrid } from 'naive-ui'
import { computed, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { teamsApi, usersApi } from '@/api/accounts'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { useAction } from '@/composables/useAction'
import { useAuthStore } from '@/stores/auth'
import type { Team, TeamRef, User, UserRef } from '@/types/accounts'
import type { Id } from '@/types/common'

/**
 * Who is responsible for a request or a problem report: a team, a person, both or
 * neither. Every change is saved right away through `assign`.
 */
const props = defineProps<{
  team: TeamRef | null
  assignee: UserRef | null
  assign: (data: { team: Id | null; assignee: Id | null }) => Promise<T>
}>()
const emit = defineEmits<{ updated: [record: T] }>()
const { t } = useI18n()
const auth = useAuthStore()
const { busy, run } = useAction()

const team = ref<Id | null>(props.team?.id ?? null)
const assignee = ref<Id | null>(props.assignee?.id ?? null)
/** Members of the chosen team, listed first when picking a person. */
const memberIds = ref(new Set<Id>())

onMounted(async () => {
  if (team.value)
    memberIds.value = new Set((await teamsApi.get(team.value)).members.map((m) => m.id))
})

// Refs carry what the select labels need (name / display_name).
const initialTeam = computed(() => props.team as Team | null)
const initialAssignee = computed(() => props.assignee as User | null)
const isMine = computed(() => assignee.value === auth.user?.id)

async function save() {
  const updated = await run(
    () => props.assign({ team: team.value, assignee: assignee.value }),
    t('common.saved'),
  )
  if (updated) emit('updated', updated)
  else {
    team.value = props.team?.id ?? null
    assignee.value = props.assignee?.id ?? null
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
  <NForm label-placement="top" size="medium" :show-feedback="false">
    <NGrid :cols="2" :x-gap="12" :y-gap="8" item-responsive responsive="self">
      <NFormItemGi span="2 400:1" :label="t('common.assignment.team')">
        <EntitySelect
          v-model="team"
          :fetcher="teamsApi.list"
          :label="(item: Team) => item.name"
          :initial="initialTeam"
          :placeholder="t('common.assignment.noTeam')"
          :disabled="busy"
          @select="onTeam"
        />
      </NFormItemGi>
      <NFormItemGi span="2 400:1">
        <template #label>
          <span class="assignee-label">
            {{ t('common.assignment.assignee') }}
            <NButton v-if="!isMine" text size="tiny" type="primary" @click="assignToMe">
              <template #icon><UserRoundPlus :size="13" /></template>
              {{ t('common.assignment.assignToMe') }}
            </NButton>
          </span>
        </template>
        <EntitySelect
          v-model="assignee"
          :fetcher="usersApi.list"
          :params="{ is_staff: true, is_active: true }"
          :label="(item: User) => item.display_name"
          :initial="initialAssignee"
          :prefer="(item: User) => memberIds.has(item.id)"
          :placeholder="t('common.assignment.nobody')"
          :disabled="busy"
          @select="save"
        />
      </NFormItemGi>
    </NGrid>
  </NForm>
</template>

<style scoped>
.assignee-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  width: 100%;
}
/* As tall as the plain label next to it (the button overflows), so both selects line up. */
.assignee-label {
  height: 1lh;
}
</style>
