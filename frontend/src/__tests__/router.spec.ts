import { createPinia, setActivePinia } from 'pinia'
import { beforeAll, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import type { RouteRecordRaw } from 'vue-router'

import { ApiError } from '@/api/client'
import router from '@/router'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'

import { makeSiteSettings, makeUser } from './helpers'

const api = vi.hoisted(() => ({
  me: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  siteGet: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  unauthorized: null as (() => void) | null,
}))

vi.mock('@/api/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/auth')>()),
  authApi: { me: api.me },
}))
vi.mock('@/api/settings', () => ({ siteSettingsApi: { get: api.siteGet } }))
vi.mock('@/api/client', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/client')>()),
  onUnauthorized: (handler: () => void) => (api.unauthorized = handler),
}))

// Small stand-in routes with the same meta flags as the real ones.
vi.mock('@/router/routes', () => {
  const page = defineComponent({ render: () => h('div') })
  const routes: RouteRecordRaw[] = [
    {
      path: '/login',
      name: 'login',
      component: page,
      meta: { public: true, title: 'auth.signIn' },
    },
    { path: '/help', name: 'help', component: page, meta: { public: true } },
    { path: '/', name: 'dashboard', component: page },
    { path: '/terminal', name: 'terminal', component: page, meta: { terminal: true } },
    { path: '/assets', name: 'assets', component: page, meta: { it: true, permission: 'assets' } },
    { path: '/reports', name: 'reports', component: page, meta: { it: true } },
    { path: '/approvals', name: 'approvals', component: page, meta: { approver: true } },
    { path: '/admin', name: 'admin', component: page, meta: { superuser: true } },
    { path: '/orders', name: 'orders', component: page, meta: { module: 'procurement' } },
    { path: '/profile', name: 'profile', component: page },
  ]
  return { routes }
})

// jsdom does not scroll; the router scrolls to the top after each navigation.
beforeAll(() => {
  vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
})

/** Where a visit to `path` ends up. */
async function visit(path: string) {
  // Start from a neutral page so every visit is a real navigation.
  await router.push('/help')
  await router.push(path)
  return router.currentRoute.value
}

function signIn(overrides: Parameters<typeof makeUser>[0] = {}) {
  const auth = useAuthStore()
  auth.user = makeUser(overrides)
  auth.checked = true
  useFeaturesStore().settings = makeSiteSettings()
}

describe('router guard', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    api.me.mockReset().mockRejectedValue(new ApiError(401, 'Not logged in.'))
    api.siteGet.mockReset().mockResolvedValue(makeSiteSettings())
  })

  it('asks the server once who is signed in', async () => {
    await visit('/profile')
    await visit('/profile')
    expect(api.me).toHaveBeenCalledOnce()
    expect(useAuthStore().checked).toBe(true)
  })

  it('sends visitors to the login and back afterwards', async () => {
    const route = await visit('/profile?tab=security')
    expect(route.name).toBe('login')
    expect(route.query.next).toBe('/profile?tab=security')
  })

  it('does not add the start page as the way back', async () => {
    const route = await visit('/')
    expect(route.name).toBe('login')
    expect(route.query).toEqual({})
  })

  it('lets visitors see public pages', async () => {
    expect((await visit('/login')).name).toBe('login')
  })

  it('sends signed-in users from the login to the dashboard', async () => {
    api.me.mockResolvedValue(makeUser())
    expect((await visit('/login')).name).toBe('dashboard')
  })

  it('sends the terminal account from the login to the terminal', async () => {
    api.me.mockResolvedValue(makeUser({ is_terminal: true }))
    expect((await visit('/login')).name).toBe('terminal')
  })

  it('keeps the terminal account on terminal pages', async () => {
    signIn({ is_terminal: true })
    expect((await visit('/terminal')).name).toBe('terminal')
    expect((await visit('/profile')).name).toBe('terminal')
  })

  it('loads the site settings once before the first page', async () => {
    const auth = useAuthStore()
    auth.user = makeUser()
    auth.checked = true
    await visit('/profile')
    await visit('/')
    expect(api.siteGet).toHaveBeenCalledOnce()
  })

  it('still opens the page when the site settings cannot be loaded', async () => {
    api.siteGet.mockRejectedValue(new ApiError(0, 'unreachable'))
    const auth = useAuthStore()
    auth.user = makeUser()
    auth.checked = true
    expect((await visit('/profile')).name).toBe('profile')
  })

  it('keeps employees out of IT and terminal pages', async () => {
    signIn({ permissions: { assets: 'write' } })
    expect((await visit('/reports')).name).toBe('dashboard')
    expect((await visit('/terminal')).name).toBe('dashboard')
  })

  it('lets IT staff open the terminal', async () => {
    signIn({ is_it_staff: true })
    expect((await visit('/terminal')).name).toBe('terminal')
  })

  it('needs the right of the area', async () => {
    signIn({ is_it_staff: true })
    expect((await visit('/assets')).name).toBe('dashboard')
    signIn({ is_it_staff: true, permissions: { assets: 'read' } })
    expect((await visit('/assets')).name).toBe('assets')
  })

  it('keeps approver pages for approvers', async () => {
    signIn()
    expect((await visit('/approvals')).name).toBe('dashboard')
    signIn({ is_approver: true })
    expect((await visit('/approvals')).name).toBe('approvals')
  })

  it('keeps administration for superusers', async () => {
    signIn({ is_it_staff: true })
    expect((await visit('/admin')).name).toBe('dashboard')
    signIn({ is_superuser: true })
    expect((await visit('/admin')).name).toBe('admin')
  })

  it('hides pages of switched-off modules', async () => {
    signIn()
    expect((await visit('/orders')).name).toBe('orders')
    useFeaturesStore().settings = makeSiteSettings({ procurement: false })
    expect((await visit('/orders')).name).toBe('dashboard')
  })

  it('sets the page title', async () => {
    await visit('/login')
    expect(document.title).toBe('Sign in · Argus')
    await visit('/help')
    expect(document.title).toBe('Argus')
  })
})

describe('expired session', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    api.siteGet.mockReset().mockResolvedValue(makeSiteSettings())
  })

  it('signs out and returns to the login with the way back', async () => {
    signIn()
    await visit('/profile')
    api.unauthorized!()
    await vi.waitFor(() => expect(router.currentRoute.value.name).toBe('login'))
    expect(router.currentRoute.value.query).toEqual({ next: '/profile' })
    expect(useAuthStore().isAuthenticated).toBe(false)
    expect(useAuthStore().endReason).toBe('expired')
  })

  it('ignores calls that fail after a sign-out', async () => {
    signIn()
    await visit('/profile')
    const auth = useAuthStore()
    auth.user = null
    auth.endReason = 'signedOut'
    await visit('/login')
    api.unauthorized!()
    await Promise.resolve()
    expect(router.currentRoute.value.fullPath).toBe('/login')
    expect(auth.endReason).toBe('signedOut')
  })

  it('stays on a public page', async () => {
    api.me.mockReset().mockRejectedValue(new ApiError(401, ''))
    await visit('/help')
    api.unauthorized!()
    await Promise.resolve()
    expect(router.currentRoute.value.name).toBe('help')
  })
})
