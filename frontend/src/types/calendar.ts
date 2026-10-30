import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'

export const CALENDAR_KINDS = allValues<Schemas['CalendarEntryOut']['kind']>({
  loan: true,
  pickup: true,
  return: true,
  delivery: true,
  warranty: true,
  license: true,
})
