import type { CalendarEntry, CalendarKind } from '@/types/calendar'

import { http } from './client'

export const calendarApi = {
  entries: (start: string, end: string, kinds: CalendarKind[]) =>
    http.get<CalendarEntry[]>('/calendar', { start, end, kinds }),
}
