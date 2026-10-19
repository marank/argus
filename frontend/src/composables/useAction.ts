import { useMessage } from 'naive-ui'
import { ref } from 'vue'

import { ApiError } from '@/api/client'

/**
 * Wrap an async action with a loading flag and error toast.
 * Returns `undefined` when the action failed.
 */
export function useAction() {
  const message = useMessage()
  const busy = ref(false)

  async function run<T>(action: () => Promise<T>, success?: string): Promise<T | undefined> {
    busy.value = true
    try {
      const result = await action()
      if (success) message.success(success)
      return result
    } catch (error) {
      message.error(error instanceof ApiError ? error.message : String(error), { duration: 6000 })
      return undefined
    } finally {
      busy.value = false
    }
  }

  return { busy, run }
}
