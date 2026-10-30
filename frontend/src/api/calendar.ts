import type { Schemas } from '@/api/types'

import { http } from './client'

export const calendarApi = {
  entries: (
    start: string,
    end: string,
    kinds: Schemas['CalendarEntryOut']['kind'][],
    assigned?: string | null,
  ) =>
    http.get<Schemas['CalendarEntryOut'][]>('/calendar', {
      start,
      end,
      kinds,
      assigned: assigned ?? undefined,
    }),
}
