import type { LdapSettings, LdapSettingsInput, LdapTestResult } from '@/types/settings'

import { http } from './client'

export const ldapSettingsApi = {
  get: () => http.get<LdapSettings>('/settings/ldap'),
  update: (data: LdapSettingsInput) => http.put<LdapSettings>('/settings/ldap', data),
  test: (data: LdapSettingsInput & { username: string }) =>
    http.post<LdapTestResult>('/settings/ldap/test', data),
}
