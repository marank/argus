<script setup lang="ts">
import { UserRoundPlus } from '@lucide/vue'
import { NButton, NForm, NFormItemGi, NGrid } from 'naive-ui'
import { onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { teamsApi, usersApi } from '@/api/accounts'
import EntitySelect from '@/components/common/EntitySelect.vue'
import type { AssignmentForm } from '@/composables/useAssignment'
import type { Schemas } from '@/api/types'
import type { Id } from '@/types/common'

/**
 * Who is responsible for a request or a problem report: a team, a person, both or
 * neither. The picks stay in `form` until the surrounding card saves them; only
 * "Assign to me" saves right away.
 */
const props = defineProps<{
  team: Schemas['TeamRefOut'] | null
  assignee: Schemas['UserRefOut'] | null
  form: AssignmentForm
}>()
const { t } = useI18n()

/** Members of the chosen team, listed first when picking a person. */
const memberIds = ref(new Set<Id>())

onMounted(async () => {
  const team = props.form.team
  if (team) memberIds.value = new Set((await teamsApi.get(team)).members.map((m) => m.id))
})

/** The selects pick one entry; the shared model type also allows several. */
const single = (value: Id | Id[] | null) => (Array.isArray(value) ? null : value)

// The select lists full teams; the reference passed as `initial` has no members.
function onTeam(selected: Schemas['TeamOut'] | Schemas['TeamRefOut'] | null) {
  memberIds.value = new Set(
    selected && 'members' in selected ? selected.members.map((m) => m.id) : [],
  )
}
</script>

<template>
  <NForm label-placement="top" size="medium" :show-feedback="false">
    <NGrid :cols="2" :x-gap="12" :y-gap="8" item-responsive responsive="self">
      <NFormItemGi span="2 400:1" :label="t('common.assignment.team')">
        <EntitySelect
          :model-value="form.team"
          @update:model-value="(v: Id | Id[] | null) => form.setTeam(single(v))"
          :fetcher="teamsApi.list"
          :label="(item: Schemas['TeamOut'] | Schemas['TeamRefOut']) => item.name"
          :initial="props.team"
          :placeholder="t('common.assignment.noTeam')"
          :disabled="form.busy"
          @select="onTeam"
        />
      </NFormItemGi>
      <NFormItemGi span="2 400:1">
        <template #label>
          <span class="assignee-label">
            {{ t('common.assignment.assignee') }}
            <NButton
              v-if="!form.isMine"
              text
              size="tiny"
              type="primary"
              :disabled="form.busy"
              @click="form.assignToMe"
            >
              <template #icon><UserRoundPlus :size="13" /></template>
              {{ t('common.assignment.assignToMe') }}
            </NButton>
          </span>
        </template>
        <EntitySelect
          :model-value="form.assignee"
          @update:model-value="(v: Id | Id[] | null) => form.setAssignee(single(v))"
          :fetcher="usersApi.list"
          :params="{ is_staff: true, is_active: true }"
          :label="(item: Schemas['UserOut'] | Schemas['UserRefOut']) => item.display_name"
          :initial="props.assignee"
          :prefer="(item: Schemas['UserOut'] | Schemas['UserRefOut']) => memberIds.has(item.id)"
          :placeholder="t('common.assignment.nobody')"
          :disabled="form.busy"
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
