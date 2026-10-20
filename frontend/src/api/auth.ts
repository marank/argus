import type {
  CurrentUser,
  TwoFactorChallenge,
  TwoFactorMethod,
  TwoFactorSetup,
  TwoFactorStatus,
} from '@/types/accounts'

import { ensureCsrfCookie, http } from './client'

export const authApi = {
  /** Signs in, or answers with the second step when the user switched it on. */
  async login(username: string, password: string) {
    await ensureCsrfCookie()
    return http.post<CurrentUser | TwoFactorChallenge>('/auth/login', { username, password })
  },
  verifyLogin: (code: string) => http.post<CurrentUser>('/auth/login/verify', { code }),
  resendLoginCode: () => http.post<TwoFactorChallenge>('/auth/login/resend'),
  logout: () => http.post<void>('/auth/logout'),
  me: () => http.get<CurrentUser>('/auth/me'),
  updatePreferences: (
    data: Partial<Pick<CurrentUser, 'language' | 'notification_settings' | 'dashboard_settings'>>,
  ) => http.patch<CurrentUser>('/auth/me', data),
}

export const isChallenge = (
  result: CurrentUser | TwoFactorChallenge,
): result is TwoFactorChallenge => !('id' in result)

type BackupCodes = { backup_codes: string[] }

/** The user's own two-factor sign-in. */
export const twoFactorApi = {
  status: () => http.get<TwoFactorStatus>('/auth/two-factor'),
  setup: (method: TwoFactorMethod, password: string) =>
    http.post<TwoFactorSetup>('/auth/two-factor/setup', { method, password }),
  resendSetupCode: () => http.post<TwoFactorSetup>('/auth/two-factor/setup/resend'),
  confirm: (code: string) => http.post<BackupCodes>('/auth/two-factor/setup/confirm', { code }),
  renewBackupCodes: (password: string) =>
    http.post<BackupCodes>('/auth/two-factor/backup-codes', { password }),
  disable: (password: string) => http.post<void>('/auth/two-factor/disable', { password }),
}
