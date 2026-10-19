export type CalendarKind = 'loan' | 'pickup' | 'return' | 'delivery' | 'warranty'

export const CALENDAR_KINDS: CalendarKind[] = ['loan', 'pickup', 'return', 'delivery', 'warranty']

export interface CalendarEntry {
  id: string
  kind: CalendarKind
  title: string
  /** ISO date for all-day entries, ISO date-time otherwise. */
  start: string
  /** Exclusive end date of multi-day entries. */
  end: string | null
  all_day: boolean
  status: string
  overdue: boolean
  /** Due date of a return (differs from `start` while it is overdue). */
  due: string | null
  link: { name: string; id?: string; warranty_until?: string }
  details: string[]
}
