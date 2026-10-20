import { useDebounceFn, useDocumentVisibility } from '@vueuse/core'
import { onScopeDispose, watch } from 'vue'

import { useLiveStore, type LiveEvent } from '@/stores/live'

/**
 * Calls `reload` when a live update signal for one of `topics` arrives (see
 * `stores/live`), e.g. `useLive(['reservation'], load)`.
 *
 * - `id`: only signals for this object (or for the whole topic) count.
 * - `paused`: while true, e.g. with a form or modal open, signals are held back
 *   and one reload follows once it turns false. A hidden tab waits likewise.
 *
 * Several signals in a row cause a single reload.
 */
export function useLive(
  topics: string[],
  reload: () => unknown,
  options: { id?: () => string | null | undefined; paused?: () => boolean } = {},
) {
  const live = useLiveStore()
  const visibility = useDocumentVisibility()
  let pending = false

  const waiting = () => visibility.value === 'hidden' || (options.paused?.() ?? false)
  const run = useDebounceFn(() => {
    if (waiting()) pending = true
    else reload()
  }, 300)

  function matches(event: LiveEvent): boolean {
    if (event.topic === '*') return true
    if (!topics.includes(event.topic)) return false
    const id = options.id?.()
    return !id || !event.id || event.id === id
  }

  const unsubscribe = live.subscribe((event) => {
    if (matches(event)) run()
  })
  watch(waiting, (now) => {
    if (!now && pending) {
      pending = false
      reload()
    }
  })
  onScopeDispose(unsubscribe)
}
