import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import FeatureSettingsView from '@/views/settings/FeatureSettingsView.vue'
import RulesSettingsView from '@/views/settings/RulesSettingsView.vue'
import SettingsView from '@/views/settings/SettingsView.vue'
import SiteNotificationsView from '@/views/settings/SiteNotificationsView.vue'

import { DEFAULT_RULES, makeSiteSettings, makeUser } from './helpers'
import { click, typeInto } from './dom'
import { link, mountView, pageText } from './layoutHelpers'

const api = vi.hoisted(() => ({
  site: vi.fn<() => Promise<unknown>>(),
  updateSite: vi.fn<(data: Partial<Schemas['SiteSettingsIn']>) => Promise<unknown>>(),
  notifications: vi.fn<() => Promise<unknown>>(),
  updateNotifications: vi.fn<(data: object) => Promise<unknown>>(),
}))
vi.mock('@/api/settings', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/settings')>()),
  siteSettingsApi: { get: api.site, update: api.updateSite },
  notificationSettingsApi: { get: api.notifications, update: api.updateNotifications },
}))

const admin = () => makeUser({ is_it_staff: true, is_superuser: true })

const DEFINITIONS: Schemas['FlagOut'][] = [
  { key: 'procurement', kind: 'module', requires: [] },
  { key: 'calendar', kind: 'module', requires: [] },
  { key: 'calendar_warranty', kind: 'feature', requires: ['calendar'] },
  { key: 'calendar_deliveries', kind: 'feature', requires: ['calendar', 'procurement'] },
  { key: 'attention_motion', kind: 'feature', requires: [] },
]

/** Site settings as the server stores them; `stored` holds the switches as set. */
const site = (stored: Record<string, boolean>, fields: Partial<Schemas['SiteSettingsOut']> = {}) =>
  makeSiteSettings(stored, { definitions: DEFINITIONS, ...fields })

/** The switch in the settings row labelled `label`, within the group titled `group`. */
function switchOf(label: string, group?: string) {
  const groups = [...document.body.querySelectorAll('.settings-group')].filter(
    (g) => !group || g.textContent?.includes(group),
  )
  const row = groups
    .flatMap((g) => [...g.querySelectorAll('.setting-row')])
    .find((r) => r.querySelector('.label')?.textContent?.trim().startsWith(label))
  if (!row) throw new Error(`no setting "${label}"`)
  return row.querySelector<HTMLElement>('.n-switch')!
}
const isOn = (element: HTMLElement) => element.getAttribute('aria-checked') === 'true'
const isDisabled = (element: HTMLElement) => element.classList.contains('n-switch--disabled')

describe('settings', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
  })

  async function page(...args: Parameters<typeof mountView>) {
    const result = await mountView(...args)
    unmount = () => result.wrapper.unmount()
    return result
  }

  describe('menu', () => {
    it('links every section and marks the current one', async () => {
      await page(SettingsView, { user: admin(), path: '/settings/ldap/sync' })
      const entries = [...document.body.querySelectorAll('nav a')].map((a) => [
        a.querySelector('.label')?.textContent,
        a.getAttribute('href'),
        a.classList.contains('active'),
      ])
      expect(entries).toEqual([
        ['Modules & features', '/settings/features', false],
        ['Deadlines & warnings', '/settings/rules', false],
        ['Email', '/settings/mail', false],
        ['Notifications', '/settings/notifications', false],
        ['LDAP login', '/settings/ldap', true],
      ])
    })
  })

  describe('modules and features', () => {
    async function features(stored: Record<string, boolean>) {
      api.site.mockResolvedValue(site(stored))
      api.updateSite.mockImplementation(async ({ flags }) => site({ ...stored, ...flags }))
      return page(FeatureSettingsView, { user: admin(), siteUnloaded: true })
    }

    it('lists each feature under the first module it needs', async () => {
      await features({})
      const groups = [...document.body.querySelectorAll('.setting-row .label')].map((l) =>
        l.textContent?.trim(),
      )
      expect(groups).toEqual([
        'Module enabled',
        'Module enabled',
        'Warranty ends in the calendar',
        'Deliveries in the calendar',
        'Attention animations',
      ])
      expect(pageText()).toContain('General')
    })

    it('switches a module on with exactly its flag', async () => {
      await features({ procurement: false })
      expect(isOn(switchOf('Module enabled', 'Procurement'))).toBe(false)
      await click(switchOf('Module enabled', 'Procurement'))
      expect(api.updateSite).toHaveBeenCalledWith({ flags: { procurement: true } })
      expect(pageText()).toContain('Procurement enabled')
      expect(isOn(switchOf('Module enabled', 'Procurement'))).toBe(true)
    })

    it('switches a feature off', async () => {
      await features({})
      await click(switchOf('Warranty ends in the calendar'))
      expect(api.updateSite).toHaveBeenCalledWith({ flags: { calendar_warranty: false } })
      expect(pageText()).toContain('Warranty ends in the calendar disabled')
    })

    it('greys out features while a module they need is off and names it', async () => {
      await features({ procurement: false })
      const deliveries = switchOf('Deliveries in the calendar')
      expect(isDisabled(deliveries)).toBe(true)
      expect(isDisabled(switchOf('Warranty ends in the calendar'))).toBe(false)
      expect(deliveries.parentElement?.textContent).toContain('requires Procurement')
    })

    it('does not name the module a feature is listed under', async () => {
      await features({ calendar: false })
      expect(isDisabled(switchOf('Deliveries in the calendar'))).toBe(true)
      expect(pageText()).not.toContain('requires')
    })

    it('says when switching failed and keeps the switch', async () => {
      await features({})
      api.updateSite.mockRejectedValue(new ApiError(500, 'HTTP 500'))
      await click(switchOf('Attention animations'))
      expect(pageText()).toContain('An error occurred')
      expect(isOn(switchOf('Attention animations'))).toBe(true)
    })
  })

  describe('site notifications', () => {
    const events: Schemas['NotificationEventOut'][] = [
      { key: 'request_confirmed', audience: 'employee', mail: true, app: true },
      { key: 'approval_requested', audience: 'approver', mail: true, app: true },
      { key: 'request_submitted', audience: 'it', mail: true, app: false },
    ]

    async function notifications(mailReady = true) {
      api.notifications.mockResolvedValue({
        mail: { request_confirmed: true, approval_requested: true, request_submitted: true },
        app: { request_confirmed: true, approval_requested: false, request_submitted: false },
        mail_ready: mailReady,
      })
      api.updateNotifications.mockImplementation(async (data) => ({ ...data, mail_ready: true }))
      api.site.mockResolvedValue(site({}, { notifications: events }))
      return page(SiteNotificationsView, {
        user: admin(),
        site: { notifications: events },
      })
    }
    const toggle = (name: string) =>
      document.body.querySelector<HTMLElement>(`.n-switch[aria-label="${name}"]`)!

    it('shows each kind by audience with a switch per channel', async () => {
      await notifications()
      expect(pageText()).toContain('To employees')
      expect(pageText()).toContain('To approvers')
      expect(pageText()).toContain('To IT')
      expect(isOn(toggle('New request: Email'))).toBe(true)
      expect(isOn(toggle('New request: In the app'))).toBe(false)
    })

    it('saves both channels as switched', async () => {
      await notifications()
      await click(toggle('Request confirmed: Email'))
      await click(toggle('Approval needed: In the app'))
      expect(api.updateNotifications).not.toHaveBeenCalled()
      await click('Save')
      expect(api.updateNotifications).toHaveBeenCalledWith({
        mail: { request_confirmed: false, approval_requested: true, request_submitted: true },
        app: { request_confirmed: true, approval_requested: true, request_submitted: false },
      })
      expect(pageText()).toContain('Saved')
    })

    it('points to the mail setup while email is not ready', async () => {
      await notifications(false)
      expect(pageText()).toContain('Email is not set up yet')
      expect(link('Email').getAttribute('href')).toBe('/settings/mail')
    })
  })

  describe('deadlines', () => {
    it('saves the changed periods with the others', async () => {
      api.site.mockResolvedValue(site({}, { rules: DEFAULT_RULES }))
      api.updateSite.mockImplementation(async ({ rules }) => site({}, { rules: rules! }))
      await page(RulesSettingsView, { user: admin(), siteUnloaded: true })
      const loan = document.body.querySelector<HTMLInputElement>('.setting-row input')!
      expect(loan.value).toBe('5')
      await typeInto(loan, '10')
      // A number field takes the value when it is left, as clicking "Save" does.
      loan.dispatchEvent(new FocusEvent('blur'))
      await click('Save')
      expect(api.updateSite).toHaveBeenCalledWith({
        rules: { ...DEFAULT_RULES, default_loan_days: 10 },
      })
    })
  })
})
