import { Bell, CalendarClock, KeyRound, Mail, ToggleRight } from '@lucide/vue'
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
    name: 'settings-features',
    label: 'settings.sections.features',
    description: 'settings.sections.featuresDescription',
    icon: ToggleRight,
  },
  {
    name: 'settings-rules',
    label: 'settings.sections.rules',
    description: 'settings.sections.rulesDescription',
    icon: CalendarClock,
  },
  {
    name: 'settings-mail',
    label: 'settings.sections.mail',
    description: 'settings.sections.mailDescription',
    icon: Mail,
  },
  {
    name: 'settings-notifications',
    label: 'settings.sections.notifications',
    description: 'settings.sections.notificationsDescription',
    icon: Bell,
  },
  {
    name: 'settings-ldap',
    label: 'settings.sections.ldap',
    description: 'settings.sections.ldapDescription',
    icon: KeyRound,
  },
]
