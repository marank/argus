import type { Schemas } from '@/api/types'

export const CALENDAR_KINDS: Schemas['CalendarEntryOut']['kind'][] = [
  'loan',
  'pickup',
  'return',
  'delivery',
  'warranty',
  'license',
]
