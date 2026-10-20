import { computed, shallowRef, watch, type WritableComputedRef } from 'vue'

type Options = () => Record<string, unknown>
type Save = (options: Record<string, unknown>) => void

/**
 * One setting a widget keeps in its stored `options`, as a writable value. A
 * change shows at once and is saved through `save` (the widget's
 * `update:options`); stored values that `valid` rejects read as `fallback`.
 */
export function useOption<T>(
  options: Options,
  save: Save,
  key: string,
  fallback: T,
  valid: (value: unknown) => value is T,
): WritableComputedRef<T> {
  // Saving takes a round trip; until the saved options come back the choice shows anyway.
  const chosen = shallowRef<{ value: T } | null>(null)
  watch(options, () => (chosen.value = null))
  return computed({
    get: () => {
      if (chosen.value) return chosen.value.value
      const stored = options()[key]
      return valid(stored) ? stored : fallback
    },
    set: (value) => {
      chosen.value = { value }
      save({ ...options(), [key]: value })
    },
  })
}

/** A guard for `useOption` accepting one of the given values. */
export const oneOf =
  <T>(values: readonly T[]) =>
  (value: unknown): value is T =>
    values.includes(value as T)

/** A guard for `useOption` accepting a list of the given values. */
export const someOf =
  <T>(values: readonly T[]) =>
  (value: unknown): value is T[] =>
    Array.isArray(value) && value.every((v) => values.includes(v as T))

export const isBoolean = (value: unknown): value is boolean => typeof value === 'boolean'

/** The look-ahead periods the list widgets offer, in days. */
export const PERIODS = [3, 7, 14] as const
export type Period = (typeof PERIODS)[number]
