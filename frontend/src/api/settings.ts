import type {
  FlagKey,
  LdapSettings,
  LdapSettingsInput,
  LdapTestResult,
  MailSettings,
  MailSettingsInput,
  NotificationSettings,
  Rules,
  SiteSettings,
} from '@/types/settings'

import { http } from './client'

export const ldapSettingsApi = {
  get: () => http.get<LdapSettings>('/settings/ldap'),
  update: (data: LdapSettingsInput) => http.put<LdapSettings>('/settings/ldap', data),
  test: (data: LdapSettingsInput & { username: string }) =>
    http.post<LdapTestResult>('/settings/ldap/test', data),
}

export const siteSettingsApi = {
  get: () => http.get<SiteSettings>('/settings/site'),
  update: (data: { flags?: Partial<Record<FlagKey, boolean>>; rules?: Rules }) =>
    http.put<SiteSettings>('/settings/site', data),
}

export const notificationSettingsApi = {
  get: () => http.get<NotificationSettings>('/settings/notifications'),
  update: (data: Pick<NotificationSettings, 'mail' | 'app'>) =>
    http.put<NotificationSettings>('/settings/notifications', data),
}

export const mailSettingsApi = {
  get: () => http.get<MailSettings>('/settings/mail'),
  update: (data: MailSettingsInput) => http.put<MailSettings>('/settings/mail', data),
  test: (to: string) => http.post<{ detail: string }>('/settings/mail/test', { to }),
}
