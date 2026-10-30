import type { Schemas } from '@/api/types'

import { http } from './client'

export const ldapSettingsApi = {
  get: () => http.get<Schemas['LdapSettingsOut']>('/settings/ldap'),
  update: (data: Schemas['LdapSettingsIn']) =>
    http.put<Schemas['LdapSettingsOut']>('/settings/ldap', data),
  test: (data: Schemas['LdapSettingsIn'] & { username: string }) =>
    http.post<Schemas['LdapTestOut']>('/settings/ldap/test', data),
  syncPreview: (query: Schemas['LdapSyncQueryIn']) =>
    http.post<Schemas['LdapSyncPreviewOut']>('/settings/ldap/sync/preview', query),
  syncApply: (query: Schemas['LdapSyncQueryIn'] & { dns: string[] }) =>
    http.post<Schemas['LdapSyncResultOut']>('/settings/ldap/sync/apply', query),
}

export const siteSettingsApi = {
  get: () => http.get<Schemas['SiteSettingsOut']>('/settings/site'),
  update: (data: Partial<Schemas['SiteSettingsIn']>) =>
    http.put<Schemas['SiteSettingsOut']>('/settings/site', data),
}

export const notificationSettingsApi = {
  get: () => http.get<Schemas['NotificationSettingsOut']>('/settings/notifications'),
  update: (data: Pick<Schemas['NotificationSettingsOut'], 'mail' | 'app'>) =>
    http.put<Schemas['NotificationSettingsOut']>('/settings/notifications', data),
}

export const mailSettingsApi = {
  get: () => http.get<Schemas['MailSettingsOut']>('/settings/mail'),
  update: (data: Schemas['MailSettingsIn']) =>
    http.put<Schemas['MailSettingsOut']>('/settings/mail', data),
  test: (to: string) => http.post<{ detail: string }>('/settings/mail/test', { to }),
}
