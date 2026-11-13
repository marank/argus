import type { Schemas } from '@/api/types'

import { ensureCsrfCookie, http } from './client'

export const authApi = {
  /** Signs in, or answers with the second step when the user switched it on. */
  async login(username: string, password: string) {
    await ensureCsrfCookie()
    return http.post<Schemas['CurrentUserOut'] | Schemas['TwoFactorChallengeOut']>('/auth/login', {
      username,
      password,
    })
  },
  verifyLogin: (code: string) =>
    http.post<Schemas['CurrentUserOut']>('/auth/login/verify', { code }),
  resendLoginCode: () => http.post<Schemas['TwoFactorChallengeOut']>('/auth/login/resend'),
  logout: () => http.post<void>('/auth/logout'),
  me: () => http.get<Schemas['CurrentUserOut']>('/auth/me'),
  /** Whether the server and its database answer; the login page asks before signing in. */
  health: () => http.get<{ status: string }>('/health'),
  updatePreferences: (
    data: Partial<
      Pick<
        Schemas['CurrentUserOut'],
        | 'language'
        | 'theme'
        | 'notification_settings'
        | 'app_notification_settings'
        | 'dashboard_settings'
      >
    >,
  ) => http.patch<Schemas['CurrentUserOut']>('/auth/me', data),
}

export const isChallenge = (
  result: Schemas['CurrentUserOut'] | Schemas['TwoFactorChallengeOut'],
): result is Schemas['TwoFactorChallengeOut'] => !('id' in result)

type BackupCodes = { backup_codes: string[] }

/** The user's own password (local accounts). */
export const passwordApi = {
  change: (currentPassword: string, newPassword: string) =>
    http.post<void>('/auth/password', {
      current_password: currentPassword,
      new_password: newPassword,
    }),
}

/** The user's own two-factor sign-in. */
export const twoFactorApi = {
  status: () => http.get<Schemas['TwoFactorStatusOut']>('/auth/two-factor'),
  setup: (method: Schemas['TwoFactorMethod'], password: string) =>
    http.post<Schemas['TwoFactorSetupOut']>('/auth/two-factor/setup', { method, password }),
  resendSetupCode: () => http.post<Schemas['TwoFactorSetupOut']>('/auth/two-factor/setup/resend'),
  confirm: (code: string) => http.post<BackupCodes>('/auth/two-factor/setup/confirm', { code }),
  renewBackupCodes: (password: string) =>
    http.post<BackupCodes>('/auth/two-factor/backup-codes', { password }),
  disable: (password: string) => http.post<void>('/auth/two-factor/disable', { password }),
}
