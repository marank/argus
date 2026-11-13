import { mount } from '@vue/test-utils'
import { defineComponent, type Plugin } from 'vue'

import type { Schemas } from '@/api/types'

type CurrentUser = Schemas['CurrentUserOut']
type SiteSettings = Schemas['SiteSettingsOut']

/** A signed-in employee without special roles; override what the test is about. */
export function makeUser(overrides: Partial<CurrentUser> = {}): CurrentUser {
  return {
    id: 'u1',
    username: 'jdoe',
    display_name: 'Jane Doe',
    language: 'en',
    theme: 'system',
    is_it_staff: false,
    is_superuser: false,
    is_terminal: false,
    is_approver: false,
    permissions: {},
    notification_settings: {},
    app_notification_settings: {},
    dashboard_settings: { widgets: [] },
    ...overrides,
  } as unknown as CurrentUser
}

export const DEFAULT_RULES: Schemas['RulesSchema'] = {
  warranty_warning_days: 60,
  license_warning_days: 60,
  default_loan_days: 5,
  max_loan_days: 0,
  return_reminder_days: 2,
  session_hours: 12,
}

/** Site settings with the given flags; flags not named count as on. */
export function makeSiteSettings(
  flags: Record<string, boolean> = {},
  overrides: Partial<SiteSettings> = {},
): SiteSettings {
  return {
    flags,
    stored: flags,
    definitions: [],
    rules: DEFAULT_RULES,
    mail_enabled: false,
    ldap_enabled: false,
    ...overrides,
  } as unknown as SiteSettings
}

/** Stands in for the browser's EventSource; the test plays the server. */
export class FakeEventSource {
  static CLOSED = 2
  static last: FakeEventSource
  static created = 0
  readyState = 1
  closed = false
  onopen: (() => void) | null = null
  onmessage: ((message: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  listeners: Record<string, () => void> = {}
  constructor(public url: string) {
    FakeEventSource.last = this
    FakeEventSource.created += 1
  }
  addEventListener(name: string, listener: () => void) {
    this.listeners[name] = listener
  }
  close() {
    this.closed = true
  }
  send(topic: string, id: string | null = null) {
    this.onmessage?.({ data: JSON.stringify({ topic, id }) })
  }
}

/** Runs a composable inside a mounted component, for those that need inject or hooks. */
export function withSetup<T>(composable: () => T, plugins: Plugin[] = []) {
  let result!: T
  const wrapper = mount(
    defineComponent({
      setup() {
        result = composable()
        return () => null
      },
    }),
    { global: { plugins } },
  )
  return { result, wrapper }
}
