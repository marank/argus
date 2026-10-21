import { reactive, watch } from 'vue'

import { ApiError } from '@/api/client'

/**
 * Validation errors of a failed save per field, shown at the field until its value changes.
 * `item(key)` gives the props for the field's NFormItem; errors without a field of the form
 * stay with the toast of `useAction`.
 */
export function useFieldErrors(form: Record<string, unknown>) {
  const errors = reactive<Record<string, string>>({})

  function clear() {
    for (const key of Object.keys(errors)) delete errors[key]
  }

  /** Takes the field errors of `error` (if any) and rethrows it, for use inside `run`. */
  function capture(error: unknown): never {
    if (error instanceof ApiError) {
      for (const [key, messages] of Object.entries(error.errors)) {
        if (key in form && messages.length) errors[key] = messages.join(' ')
      }
    }
    throw error
  }

  function item(key: string) {
    return {
      showFeedback: !!errors[key],
      feedback: errors[key],
      validationStatus: errors[key] ? ('error' as const) : undefined,
    }
  }

  watch(
    () => ({ ...form }),
    (now, before) => {
      for (const key of Object.keys(errors)) {
        if (JSON.stringify(now[key]) !== JSON.stringify(before[key])) delete errors[key]
      }
    },
  )

  return { errors, clear, capture, item }
}
