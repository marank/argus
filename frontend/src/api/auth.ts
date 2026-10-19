import type { CurrentUser } from '@/types/accounts'

import { ensureCsrfCookie, http } from './client'

export const authApi = {
  async login(username: string, password: string) {
    await ensureCsrfCookie()
    return http.post<CurrentUser>('/auth/login', { username, password })
  },
  logout: () => http.post<void>('/auth/logout'),
  me: () => http.get<CurrentUser>('/auth/me'),
  updatePreferences: (data: Partial<Pick<CurrentUser, 'language'>>) =>
    http.patch<CurrentUser>('/auth/me', data),
}
