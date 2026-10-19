import { KeyRound } from '@lucide/vue'
import type { Component } from 'vue'

export interface SettingsSection {
  /** Route name of the section page. */
  name: string
  /** i18n keys */
  label: string
  description: string
  icon: Component
}

/** Sub-pages of the settings page, in menu order. */
export const SETTINGS_SECTIONS: SettingsSection[] = [
  {
    name: 'settings-ldap',
    label: 'settings.sections.ldap',
    description: 'settings.sections.ldapDescription',
    icon: KeyRound,
  },
]
