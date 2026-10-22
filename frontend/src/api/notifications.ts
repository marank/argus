import type { Id, Page } from '@/types/common'
import type { AppNotification } from '@/types/notifications'

import { http } from './client'

/** The signed-in user's in-app notifications (the bell). */
export const notificationsApi = {
  list: (params: { page?: number; page_size?: number; unread?: boolean } = {}) =>
    http.get<Page<AppNotification>>('/notifications', params),
  unread: () => http.get<{ unread: number }>('/notifications/unread'),
  read: (id: Id) => http.post<AppNotification>(`/notifications/${id}/read`),
  readAll: () => http.post<{ unread: number }>('/notifications/read-all'),
}
