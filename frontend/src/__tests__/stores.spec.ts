import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { ApiError } from '@/api/client'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'
import { useLiveStore, type LiveEvent } from '@/stores/live'
import { useMenuCountsStore } from '@/stores/menuCounts'
import { useNotificationsStore } from '@/stores/notifications'
import { useTheme } from '@/theme/useTheme'

import { DEFAULT_RULES, FakeEventSource, makeSiteSettings, makeUser } from './helpers'

const api = vi.hoisted(() => ({
  me: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  login: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  verifyLogin: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  logout: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  updatePreferences: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  siteGet: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  siteUpdate: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  menuCounts: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  unread: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
}))

vi.mock('@/api/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/auth')>()),
  authApi: {
    me: api.me,
    login: api.login,
    verifyLogin: api.verifyLogin,
    logout: api.logout,
    updatePreferences: api.updatePreferences,
  },
}))
vi.mock('@/api/settings', () => ({
  siteSettingsApi: { get: api.siteGet, update: api.siteUpdate },
}))
vi.mock('@/api/requests', () => ({ portalApi: { menuCounts: api.menuCounts } }))
vi.mock('@/api/notifications', () => ({ notificationsApi: { unread: api.unread } }))

beforeEach(() => {
  setActivePinia(createPinia())
  Object.values(api).forEach((mock) => mock.mockReset())
})

afterEach(() => {
  i18n.global.locale.value = 'en'
  document.documentElement.lang = 'en'
})

describe('auth store', () => {
  it('is signed out until the user is known', () => {
    const auth = useAuthStore()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.checked).toBe(false)
    expect(auth.isItStaff).toBe(false)
    expect(auth.can('assets')).toBe(false)
  })

  it('loads the current user and switches to their language', async () => {
    api.me.mockResolvedValue(makeUser({ language: 'de', is_it_staff: true }))
    const auth = useAuthStore()
    await auth.fetchCurrentUser()
    expect(auth.isAuthenticated).toBe(true)
    expect(auth.isItStaff).toBe(true)
    expect(auth.checked).toBe(true)
    expect(i18n.global.locale.value).toBe('de')
    expect(document.documentElement.lang).toBe('de')
  })

  it('treats a 401 as signed out without logging an error', async () => {
    const log = vi.spyOn(console, 'error').mockImplementation(() => {})
    api.me.mockRejectedValue(new ApiError(401, 'Not logged in.'))
    const auth = useAuthStore()
    await auth.fetchCurrentUser()
    expect(auth.isAuthenticated).toBe(false)
    expect(auth.checked).toBe(true)
    expect(log).not.toHaveBeenCalled()
    log.mockRestore()
  })

  it('logs unexpected errors but still shows the login', async () => {
    const log = vi.spyOn(console, 'error').mockImplementation(() => {})
    api.me.mockRejectedValue(new ApiError(500, 'Boom'))
    const auth = useAuthStore()
    auth.user = makeUser()
    await auth.fetchCurrentUser()
    expect(auth.user).toBeNull()
    expect(auth.checked).toBe(true)
    expect(log).toHaveBeenCalledOnce()
    log.mockRestore()
  })

  it('tells read from write rights', () => {
    const auth = useAuthStore()
    auth.user = makeUser({ permissions: { assets: 'read', models: 'write' } })
    expect(auth.can('assets')).toBe(true)
    expect(auth.can('assets', 'write')).toBe(false)
    expect(auth.can('models', 'write')).toBe(true)
    expect(auth.can('suppliers')).toBe(false)
  })

  it('exposes the roles of the user', () => {
    const auth = useAuthStore()
    auth.user = makeUser({ is_superuser: true, is_terminal: true, is_approver: true })
    expect(auth.isSuperuser).toBe(true)
    expect(auth.isTerminal).toBe(true)
    expect(auth.isApprover).toBe(true)
  })

  it('signs in directly without a second step', async () => {
    api.login.mockResolvedValue(makeUser())
    const auth = useAuthStore()
    expect(await auth.login('jdoe', 'secret')).toBeNull()
    expect(api.login).toHaveBeenCalledWith('jdoe', 'secret')
    expect(auth.isAuthenticated).toBe(true)
  })

  it('returns the challenge when a second step is due and stays signed out', async () => {
    const challenge = { two_factor: 'email', code_sent: true, email_hint: 'j***@example.com' }
    api.login.mockResolvedValue(challenge)
    const auth = useAuthStore()
    expect(await auth.login('jdoe', 'secret')).toEqual(challenge)
    expect(auth.isAuthenticated).toBe(false)
  })

  it('signs in after the second step', async () => {
    api.verifyLogin.mockResolvedValue(makeUser())
    const auth = useAuthStore()
    await auth.verifyLogin('123456')
    expect(api.verifyLogin).toHaveBeenCalledWith('123456')
    expect(auth.isAuthenticated).toBe(true)
  })

  it('forgets the user on logout', async () => {
    api.logout.mockResolvedValue(undefined)
    const auth = useAuthStore()
    auth.user = makeUser()
    await auth.logout()
    expect(auth.user).toBeNull()
  })

  it('keeps the user when the logout fails', async () => {
    api.logout.mockRejectedValue(new ApiError(0, 'unreachable'))
    const auth = useAuthStore()
    auth.user = makeUser()
    await expect(auth.logout()).rejects.toThrow('unreachable')
    expect(auth.user).not.toBeNull()
  })

  it('clears the user', () => {
    const auth = useAuthStore()
    auth.user = makeUser()
    auth.clear()
    expect(auth.isAuthenticated).toBe(false)
  })

  it('switches the language right away and saves it for a signed-in user', async () => {
    api.updatePreferences.mockResolvedValue(makeUser({ language: 'de' }))
    const auth = useAuthStore()
    auth.user = makeUser()
    await auth.changeLanguage('de')
    expect(i18n.global.locale.value).toBe('de')
    expect(api.updatePreferences).toHaveBeenCalledWith({ language: 'de' })
    expect(auth.user?.language).toBe('de')
  })

  it('takes the theme from the profile and saves a new choice there', async () => {
    const { mode } = useTheme()
    api.me.mockResolvedValue(makeUser({ theme: 'dark' }))
    const auth = useAuthStore()
    await auth.fetchCurrentUser()
    expect(mode.value).toBe('dark')

    api.updatePreferences.mockResolvedValue(makeUser({ theme: 'solarized' }))
    await auth.changeTheme('solarized')
    expect(api.updatePreferences).toHaveBeenCalledWith({ theme: 'solarized' })
    await nextTick()
    expect(document.documentElement.dataset.theme).toBe('solarized')
    mode.value = 'system'
  })

  it('only switches the language locally when signed out', async () => {
    const auth = useAuthStore()
    await auth.changeLanguage('de')
    expect(i18n.global.locale.value).toBe('de')
    expect(api.updatePreferences).not.toHaveBeenCalled()
  })

  it('saves notification and dashboard preferences for a signed-in user', async () => {
    const auth = useAuthStore()
    auth.user = makeUser()
    const settings = {
      notification_settings: { request_ready: false },
      app_notification_settings: {},
    } as Parameters<typeof auth.changeNotifications>[0]
    api.updatePreferences.mockResolvedValue(makeUser(settings))
    await auth.changeNotifications(settings)
    expect(api.updatePreferences).toHaveBeenLastCalledWith(settings)
    expect(auth.user?.notification_settings).toEqual(settings.notification_settings)

    const dashboard = { widgets: [] } as unknown as Parameters<typeof auth.changeDashboard>[0]
    await auth.changeDashboard(dashboard)
    expect(api.updatePreferences).toHaveBeenLastCalledWith({ dashboard_settings: dashboard })
  })

  it('does not save preferences when signed out', async () => {
    const auth = useAuthStore()
    await auth.changeNotifications({ notification_settings: {}, app_notification_settings: {} })
    await auth.changeDashboard({ widgets: [] })
    expect(api.updatePreferences).not.toHaveBeenCalled()
  })
})

describe('features store', () => {
  afterEach(() => document.documentElement.classList.remove('no-attention-motion'))

  it('counts everything as on with default rules until loaded', () => {
    const features = useFeaturesStore()
    expect(features.isOn('procurement')).toBe(true)
    expect(features.ldapEnabled).toBe(false)
    expect(features.rules).toEqual(DEFAULT_RULES)
  })

  it('follows the loaded flags', async () => {
    api.siteGet.mockResolvedValue(makeSiteSettings({ procurement: false }, { ldap_enabled: true }))
    const features = useFeaturesStore()
    await features.load()
    expect(features.isOn('procurement')).toBe(false)
    expect(features.isOn('calendar')).toBe(true)
    expect(features.ldapEnabled).toBe(true)
  })

  it('takes the answer of an update', async () => {
    const rules = { ...DEFAULT_RULES, max_loan_days: 30 }
    api.siteUpdate.mockResolvedValueOnce(makeSiteSettings({ issues: false }))
    api.siteUpdate.mockResolvedValueOnce(makeSiteSettings({}, { rules }))
    const features = useFeaturesStore()

    await features.update({ issues: false })
    expect(api.siteUpdate).toHaveBeenLastCalledWith({ flags: { issues: false } })
    expect(features.isOn('issues')).toBe(false)

    await features.updateRules(rules)
    expect(api.siteUpdate).toHaveBeenLastCalledWith({ rules })
    expect(features.rules.max_loan_days).toBe(30)
  })

  it('switches attention animations off site-wide', async () => {
    api.siteGet.mockResolvedValue(makeSiteSettings({ attention_motion: false }))
    const features = useFeaturesStore()
    await features.load()
    await Promise.resolve()
    expect(document.documentElement.classList.contains('no-attention-motion')).toBe(true)
    features.clear()
    expect(features.settings).toBeNull()
    await Promise.resolve()
    expect(document.documentElement.classList.contains('no-attention-motion')).toBe(false)
  })
})

describe('live store', () => {
  beforeEach(() => vi.stubGlobal('EventSource', FakeEventSource))
  afterEach(() => vi.unstubAllGlobals())

  function started() {
    const live = useLiveStore()
    const events: LiveEvent[] = []
    live.subscribe((event) => events.push(event))
    live.start()
    return { live, events, source: FakeEventSource.last }
  }

  it('connects once to the event stream', () => {
    const before = FakeEventSource.created
    const { live, source } = started()
    live.start()
    expect(FakeEventSource.created - before).toBe(1)
    expect(source.url).toBe('/api/events')
    expect(live.connected).toBe(false)
    source.onopen?.()
    expect(live.connected).toBe(true)
  })

  it('passes signals on to the subscribers', () => {
    const { events, source } = started()
    source.onopen?.()
    source.send('request', 'r1')
    expect(events).toEqual([{ topic: 'request', id: 'r1' }])
  })

  it('stops passing signals on after unsubscribing', () => {
    const live = useLiveStore()
    const listener = vi.fn<(event: LiveEvent) => void>()
    const unsubscribe = live.subscribe(listener)
    live.start()
    unsubscribe()
    FakeEventSource.last.send('request', 'r1')
    expect(listener).not.toHaveBeenCalled()
  })

  it('asks to reload everything after a lost connection comes back', () => {
    const { live, events, source } = started()
    source.onopen?.()
    source.onerror?.()
    expect(live.connected).toBe(false)
    source.onopen?.()
    expect(events).toEqual([{ topic: '*', id: null }])
  })

  it('does not reload after a reconnect the server announced', () => {
    const { events, source } = started()
    source.onopen?.()
    source.listeners.bye?.()
    source.onerror?.()
    source.onopen?.()
    expect(events).toEqual([])
  })

  it('does not reload when the first connection attempt fails', () => {
    const { events, source } = started()
    source.onerror?.()
    source.onopen?.()
    expect(events).toEqual([])
  })

  it('connects anew after the server closed the stream for good', () => {
    const { live, source } = started()
    source.readyState = FakeEventSource.CLOSED
    source.onerror?.()
    live.start()
    expect(FakeEventSource.last).not.toBe(source)
  })

  it('closes the stream on stop and may start again', () => {
    const { live, source } = started()
    source.onopen?.()
    live.stop()
    expect(source.closed).toBe(true)
    expect(live.connected).toBe(false)
    live.start()
    expect(FakeEventSource.last).not.toBe(source)
  })

  it('does not reload everything after stop and start', () => {
    const { live, events, source } = started()
    source.onopen?.()
    source.onerror?.()
    live.stop()
    live.start()
    FakeEventSource.last.onopen?.()
    expect(events).toEqual([])
  })
})

describe('badge counters', () => {
  it('loads the menu counts', async () => {
    const counts = { requests: 1, approvals: 2, issues: 0, issues_updated: false }
    api.menuCounts.mockResolvedValue(counts)
    const store = useMenuCountsStore()
    await store.refresh()
    expect(store.counts).toEqual(counts)
  })

  it('keeps the last menu counts when loading fails', async () => {
    const counts = { requests: 1, approvals: 2, issues: 0, issues_updated: false }
    api.menuCounts.mockResolvedValueOnce(counts).mockRejectedValueOnce(new ApiError(0, ''))
    const store = useMenuCountsStore()
    await store.refresh()
    await expect(store.refresh()).resolves.toBeUndefined()
    expect(store.counts).toEqual(counts)
  })

  it('loads the unread notifications', async () => {
    api.unread.mockResolvedValue({ unread: 3 })
    const store = useNotificationsStore()
    expect(store.unread).toBe(0)
    await store.refresh()
    expect(store.unread).toBe(3)
  })

  it('keeps the unread number when loading fails', async () => {
    api.unread.mockResolvedValueOnce({ unread: 3 }).mockRejectedValueOnce(new Error('offline'))
    const store = useNotificationsStore()
    await store.refresh()
    await store.refresh()
    expect(store.unread).toBe(3)
  })
})
