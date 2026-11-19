import { computed, reactive, ref, watch } from 'vue'

import type { Schemas } from '@/api/types'
import { useAction } from '@/composables/useAction'
import { useAuthStore } from '@/stores/auth'
import type { Id } from '@/types/common'

export type AssignFn<T> = (data: { team: Id | null; assignee: Id | null }) => Promise<T>

/**
 * The edited assignment of a request or a problem report: team and person are picked
 * first and saved together with `save`, so the history gets one entry. "Assign to me"
 * saves right away.
 */
export function useAssignment<T>(
  current: () => { team: Schemas['TeamRefOut'] | null; assignee: Schemas['UserRefOut'] | null },
  assign: AssignFn<T>,
  onUpdated: (record: T) => void,
) {
  const auth = useAuthStore()
  const { busy, run } = useAction()

  const team = ref<Id | null>(current().team?.id ?? null)
  const assignee = ref<Id | null>(current().assignee?.id ?? null)

  const dirty = computed(
    () =>
      team.value !== (current().team?.id ?? null) ||
      assignee.value !== (current().assignee?.id ?? null),
  )
  const isMine = computed(() => assignee.value === auth.user?.id)

  async function save() {
    const updated = await run(() => assign({ team: team.value, assignee: assignee.value }))
    if (updated) onUpdated(updated)
  }

  function reset() {
    team.value = current().team?.id ?? null
    assignee.value = current().assignee?.id ?? null
  }

  // A saved or otherwise changed record replaces what was picked.
  watch(() => [current().team?.id, current().assignee?.id], reset)

  function assignToMe() {
    assignee.value = auth.user!.id
    return save()
  }

  return reactive({
    team,
    assignee,
    dirty,
    isMine,
    busy,
    setTeam: (id: Id | null) => (team.value = id),
    setAssignee: (id: Id | null) => (assignee.value = id),
    save,
    reset,
    assignToMe,
  })
}

export type AssignmentForm = ReturnType<typeof useAssignment>
