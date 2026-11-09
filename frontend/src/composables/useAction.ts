import { useMessage } from 'naive-ui'
import { ref } from 'vue'

import { ApiError } from '@/api/client'
import { focusedElement, showError, wasShownAtFields } from '@/composables/useErrorPopover'

/**
 * Wrap an async action with a loading flag. A failure shows its error at the element that
 * started the action (usually the button just clicked) unless the form already shows it at its
 * fields; `success` is for a result worth telling, not for a plain "saved".
 * Returns `undefined` when the action failed.
 */
export function useAction() {
  const message = useMessage()
  const busy = ref(false)

  async function run<T>(action: () => Promise<T>, success?: string): Promise<T | undefined> {
    const origin = focusedElement()
    busy.value = true
    try {
      const result = await action()
      if (success) message.success(success)
      return result
    } catch (error) {
      if (!wasShownAtFields(error))
        showError(error instanceof ApiError ? error.message : String(error), origin)
      return undefined
    } finally {
      busy.value = false
    }
  }

  return { busy, run }
}
