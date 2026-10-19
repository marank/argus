import type { CalendarEntry, CalendarKind } from '@/types/calendar'

import { http } from './client'

export const calendarApi = {
  entries: (start: string, end: string, kinds: CalendarKind[], assigned?: string | null) =>
    http.get<CalendarEntry[]>('/calendar', { start, end, kinds, assigned: assigned ?? undefined }),
}
