import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import NotificationSettingsView from '@/views/profile/NotificationSettingsView.vue'

import { makeSiteSettings, makeUser } from './helpers'
import { click } from './dom'
import { mountView, pageText } from './layoutHelpers'

const api = vi.hoisted(() => ({
  site: vi.fn<() => Promise<unknown>>(),
  updatePreferences: vi.fn<(data: Record<string, unknown>) => Promise<unknown>>(),
}))
vi.mock('@/api/settings', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/settings')>()),
  siteSettingsApi: { get: api.site },
}))
vi.mock('@/api/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/auth')>()),
  authApi: { updatePreferences: api.updatePreferences },
}))

type Event = Schemas['NotificationEventOut']
const event = (
  key: Event['key'],
  audience: Event['audience'],
  channels: Partial<Pick<Event, 'mail' | 'app'>> = {},
): Event => ({ key, audience, mail: true, app: true, ...channels })

const EVENTS: Event[] = [
  event('request_confirmed', 'employee'),
  event('request_ready', 'employee', { mail: false }),
  // Switched off site-wide in both channels: nothing to choose.
  event('return_reminder', 'employee', { mail: false, app: false }),
  event('approval_requested', 'approver'),
  event('request_submitted', 'it'),
]

const employee = (fields: Partial<Schemas['CurrentUserOut']> = {}) =>
  makeUser({ email: 'jane@example.com', ...fields })

const toggle = (name: string) =>
  document.body.querySelector<HTMLElement>(`.n-switch[aria-label="${name}"]`)
const state = (name: string) => {
  const element = toggle(name)!
  return {
    on: element.getAttribute('aria-checked') === 'true',
    locked: element.classList.contains('n-switch--disabled'),
  }
}

describe('own notification settings', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
    api.site.mockResolvedValue(makeSiteSettings({}, { mail_enabled: true, notifications: EVENTS }))
    api.updatePreferences.mockImplementation(async (data) => employee(data))
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
  })

  async function page(user = employee()) {
    const result = await mountView(NotificationSettingsView, { user, siteUnloaded: true })
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('names the address the emails go to', async () => {
    await page()
    expect(pageText()).toContain('by email to jane@example.com')
  })

  it('shows employees only the kinds meant for them and switched on site-wide', async () => {
    await page()
    expect(toggle('Request confirmed: Email')).not.toBeNull()
    expect(toggle('Return reminder: Email')).toBeNull()
    expect(toggle('Approval needed: Email')).toBeNull()
    expect(toggle('New request: Email')).toBeNull()
  })

  it('adds the kinds for approvers and IT to those roles', async () => {
    await page(employee({ is_approver: true, is_it_staff: true }))
    expect(toggle('Approval needed: Email')).not.toBeNull()
    expect(toggle('New request: In the app')).not.toBeNull()
  })

  it('shows a channel switched off site-wide as off and locked', async () => {
    await page()
    expect(state('Ready for pickup: Email')).toEqual({ on: false, locked: true })
    expect(state('Ready for pickup: In the app')).toEqual({ on: true, locked: false })
  })

  it('shows what the user switched off', async () => {
    await page(employee({ app_notification_settings: { request_confirmed: false } }))
    expect(state('Request confirmed: In the app').on).toBe(false)
    expect(state('Request confirmed: Email').on).toBe(true)
  })

  it('locks all email switches while mail is off on the site', async () => {
    api.site.mockResolvedValue(makeSiteSettings({}, { mail_enabled: false, notifications: EVENTS }))
    await page()
    expect(pageText()).toContain('Email delivery is currently disabled.')
    expect(state('Request confirmed: Email')).toEqual({ on: false, locked: true })
    expect(state('Request confirmed: In the app').locked).toBe(false)
  })

  it('locks all email switches without an address of their own', async () => {
    await page(employee({ email: '' }))
    expect(pageText()).toContain('Your account has no email address.')
    expect(state('Request confirmed: Email')).toEqual({ on: false, locked: true })
  })

  it('says when no notification is switched on for the user', async () => {
    api.site.mockResolvedValue(
      makeSiteSettings({}, { mail_enabled: true, notifications: [EVENTS[2]!] }),
    )
    await page()
    expect(pageText()).toContain('IT has not switched on any notifications for you')
  })

  it('saves a switch at once, keeping the other settings', async () => {
    await page(
      employee({
        notification_settings: { request_ready: false },
        app_notification_settings: { request_confirmed: true },
      }),
    )
    await click(toggle('Request confirmed: Email')!)
    expect(api.updatePreferences).toHaveBeenCalledWith({
      notification_settings: { request_ready: false, request_confirmed: false },
      app_notification_settings: { request_confirmed: true },
    })
    expect(pageText()).toContain('Saved')
  })

  it('says when saving failed', async () => {
    api.updatePreferences.mockRejectedValue(new ApiError(500, 'HTTP 500'))
    await page()
    await click(toggle('Request confirmed: In the app')!)
    expect(pageText()).toContain('An error occurred')
    expect(state('Request confirmed: In the app').on).toBe(true)
  })
})
