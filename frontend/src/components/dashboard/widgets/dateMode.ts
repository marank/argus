import { useFormat } from '@/composables/useFormat'

import { oneOf, useOption } from './options'

/** How a widget shows its dates: "Morgen, 12:00 Uhr" or "Mi., 21.10.2026, 12:00". */
export type DateMode = 'relative' | 'full'

/** The date display a widget stores in its `options.dates`. */
export function useDateMode(
  options: () => Record<string, unknown>,
  save: (options: Record<string, unknown>) => void,
  fallback: DateMode = 'relative',
) {
  const { dateWithWeekday, relativeDay } = useFormat()
  const mode = useOption<DateMode>(
    options,
    save,
    'dates',
    fallback,
    oneOf<DateMode>(['relative', 'full']),
  )

  const format = (value: string | null | undefined, as: DateMode) =>
    as === 'full' ? dateWithWeekday(value) : relativeDay(value)

  return {
    mode,
    setMode: (value: DateMode) => (mode.value = value),
    /** The date as chosen. */
    when: (value: string | null | undefined) => format(value, mode.value),
    /** The date the other way, for the tooltip. */
    other: (value: string | null | undefined) =>
      format(value, mode.value === 'full' ? 'relative' : 'full'),
  }
}
