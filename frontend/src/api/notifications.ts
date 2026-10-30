import type { Schemas } from '@/api/types'
import type { Id, Page } from '@/types/common'

import { http } from './client'

/** The signed-in user's in-app notifications (the bell). */
export const notificationsApi = {
  list: (params: { page?: number; page_size?: number; unread?: boolean } = {}) =>
    http.get<Page<Schemas['NotificationOut']>>('/notifications', params),
  unread: () => http.get<{ unread: number }>('/notifications/unread'),
  read: (id: Id) => http.post<Schemas['NotificationOut']>(`/notifications/${id}/read`),
  readAll: () => http.post<{ unread: number }>('/notifications/read-all'),
}
