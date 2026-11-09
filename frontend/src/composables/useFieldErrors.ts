import { nextTick, reactive, watch } from 'vue'

import { ApiError } from '@/api/client'
import { markShownAtFields, showFirstFieldError } from '@/composables/useErrorPopover'

/**
 * Validation errors of a failed save per field, kept until the field's value changes.
 * `item(key)` gives the props for the field's NFormItem: a red outline and the error as
 * `data-field-error`, which the error popover points at. Errors for anything that is not a field
 * of the form go to the popover at the save button (`useAction`).
 */
export function useFieldErrors(form: Record<string, unknown>) {
  const errors = reactive<Record<string, string>>({})

  function clear() {
    for (const key of Object.keys(errors)) delete errors[key]
  }

  /** Takes the field errors of `error` (if any) and rethrows it, for use inside `run`. */
  function capture(error: unknown): never {
    if (error instanceof ApiError) {
      const entries = Object.entries(error.errors).filter(([, messages]) => messages.length)
      for (const [key, messages] of entries) {
        if (key in form) errors[key] = messages.join(' ')
      }
      if (entries.length && entries.every(([key]) => key in form)) {
        markShownAtFields(error)
        void nextTick(() => showFirstFieldError())
      }
    }
    throw error
  }

  function item(key: string) {
    return {
      showFeedback: false,
      validationStatus: errors[key] ? ('error' as const) : undefined,
      'data-field-error': errors[key] || undefined,
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
