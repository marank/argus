import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

/** Quick filter of the IT lists: whose requests or reports to show. */
export type Assigned = 'me' | 'my_teams' | 'nobody' | 'all'

const VALUES: Assigned[] = ['me', 'my_teams', 'nobody', 'all']
const isAssigned = (value: unknown): value is Assigned => VALUES.includes(value as Assigned)

/**
 * The choice is remembered per list in the browser, since each IT member mostly
 * wants the same view; `?assigned=` in the URL (dashboard links) wins.
 */
export function useAssigned(storageKey: string) {
  const route = useRoute()
  const key = `argus.${storageKey}.assigned`

  function stored(): Assigned {
    try {
      const value = localStorage.getItem(key)
      return isAssigned(value) ? value : 'all'
    } catch {
      return 'all'
    }
  }

  const assigned = ref<Assigned>(isAssigned(route.query.assigned) ? route.query.assigned : stored())
  watch(assigned, (value) => {
    try {
      localStorage.setItem(key, value)
    } catch {
      // Private mode or blocked storage: the choice just is not remembered.
    }
  })
  /** The API parameter: nothing for "all". */
  const param = (value: Assigned) => (value === 'all' ? null : value)
  return { assigned, param }
}
