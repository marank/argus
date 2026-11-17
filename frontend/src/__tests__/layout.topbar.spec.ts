import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import GlobalScan from '@/components/layout/GlobalScan.vue'
import NotificationBell from '@/components/layout/NotificationBell.vue'
import UserMenu from '@/components/layout/UserMenu.vue'
import { setLocale } from '@/i18n'
import { useTheme } from '@/theme/useTheme'

import { makeUser } from './helpers'
import { click, typeInto } from './dom'
import { mountView, pageText } from './layoutHelpers'

const api = vi.hoisted(() => ({
  list: vi.fn<(params: object) => Promise<unknown>>(),
  unread: vi.fn<() => Promise<{ unread: number }>>(),
  read: vi.fn<(id: string) => Promise<unknown>>(),
  readAll: vi.fn<() => Promise<{ unread: number }>>(),
  lookup: vi.fn<(code: string) => Promise<Schemas['LookupOut']>>(),
  logout: vi.fn<() => Promise<void>>(),
  updatePreferences: vi.fn<(data: object) => Promise<unknown>>(),
}))
vi.mock('@/api/notifications', () => ({
  notificationsApi: { list: api.list, unread: api.unread, read: api.read, readAll: api.readAll },
}))
vi.mock('@/api/inventory', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/inventory')>()),
  lookupApi: { lookup: api.lookup },
}))
vi.mock('@/api/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/auth')>()),
  authApi: { logout: api.logout, updatePreferences: api.updatePreferences },
}))

const ID = (n: number) => `0192f0c4-6a3e-7b4d-9a1e-${String(n).padStart(12, '0')}`

describe('top bar', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    localStorage.clear()
  })

  async function show(...args: Parameters<typeof mountView>) {
    const result = await mountView(...args)
    unmount = () => result.wrapper.unmount()
    return result
  }

  describe('notification bell', () => {
    const notification = (
      n: number,
      fields: Partial<Schemas['NotificationOut']> = {},
    ): Schemas['NotificationOut'] => ({
      id: ID(n),
      event: 'request_ready',
      title: `Notification ${n}`,
      text: '',
      path: `/portal/requests/${ID(n)}`,
      read_at: null,
      created_at: '2026-10-29T09:00:00Z',
      ...fields,
    })
    const LIST = [
      notification(1, { text: 'Pick up at the IT desk' }),
      notification(2, { read_at: '2026-10-29T10:00:00Z', path: '' }),
    ]

    const badge = () => document.body.querySelector('.n-badge-sup')?.getAttribute('title')
    const items = () => [...document.body.querySelectorAll<HTMLButtonElement>('button.item')]

    async function bell(unread = 1) {
      api.unread.mockResolvedValue({ unread })
      api.list.mockResolvedValue({ items: LIST, count: LIST.length })
      return show(NotificationBell)
    }
    const open = () => click(document.body.querySelector('button[aria-label="Notifications"]')!)

    it.each([
      [3, '3'],
      [0, undefined],
    ])('shows %i unread notifications as %s on the bell', async (unread, number) => {
      await bell(unread)
      expect(badge()).toBe(number)
    })

    it('loads the latest notifications when opened', async () => {
      await bell()
      await open()
      expect(api.list).toHaveBeenCalledWith({ page_size: 20 })
      expect(items().map((i) => i.querySelector('.title')?.textContent)).toEqual([
        'Notification 1',
        'Notification 2',
      ])
      expect(items()[0]!.classList.contains('unread')).toBe(true)
      expect(items()[1]!.classList.contains('unread')).toBe(false)
      expect(pageText()).toContain('Pick up at the IT desk')
    })

    it('says when there are none', async () => {
      api.unread.mockResolvedValue({ unread: 0 })
      api.list.mockResolvedValue({ items: [], count: 0 })
      await show(NotificationBell)
      await open()
      expect(pageText()).toContain('No notifications.')
      expect(pageText()).not.toContain('Mark all read')
    })

    it('marks an unread one read and opens its page', async () => {
      api.read.mockResolvedValue({})
      const { router } = await bell(1)
      await open()
      // Asked again after the page change, the server has it read as well.
      api.unread.mockResolvedValue({ unread: 0 })
      await click(items()[0]!)
      expect(api.read).toHaveBeenCalledWith(ID(1))
      expect(badge()).toBeUndefined()
      expect(router.currentRoute.value.fullPath).toBe(`/portal/requests/${ID(1)}`)
    })

    it('opens a read one without marking it again, and stays without a page', async () => {
      const { router } = await bell(1)
      await open()
      await click(items()[1]!)
      expect(api.read).not.toHaveBeenCalled()
      expect(badge()).toBe('1')
      expect(router.currentRoute.value.fullPath).toBe('/')
    })

    it('asks for the true number when marking read failed', async () => {
      api.read.mockRejectedValue(new Error('offline'))
      await bell(1)
      await open()
      api.unread.mockClear().mockResolvedValue({ unread: 1 })
      await click(items()[0]!)
      expect(api.unread).toHaveBeenCalled()
      expect(badge()).toBe('1')
    })

    it('marks all read', async () => {
      api.readAll.mockResolvedValue({ unread: 0 })
      await bell(2)
      await open()
      await click('Mark all read')
      expect(api.readAll).toHaveBeenCalledOnce()
      expect(items().some((i) => i.classList.contains('unread'))).toBe(false)
      expect(badge()).toBeUndefined()
    })

    it('leads to the notification settings', async () => {
      const { router } = await bell()
      await open()
      await click(document.body.querySelector('button[aria-label="Notification settings"]')!)
      expect(router.currentRoute.value.name).toBe('profile-notifications')
    })

    it('updates the number on every page change without live updates', async () => {
      const { router } = await bell(1)
      api.unread.mockResolvedValue({ unread: 4 })
      await router.push('/portal/requests')
      await flushPromises()
      expect(badge()).toBe('4')
    })
  })

  describe('scan field', () => {
    const asset = (n: number) =>
      ({
        id: ID(n),
        inventory_number: `NB-00${n}`,
        serial_number: `SN${n}`,
        status: 'in_use',
        model: { id: ID(90), full_name: 'Dell Latitude 5550' },
      }) as Schemas['AssetOut']
    const model = { id: ID(91), full_name: 'Logitech MX Keys', ean: '5099206' }

    const field = () => document.body.querySelector<HTMLInputElement>('.scan input')!
    async function scan(code: string) {
      await typeInto(field(), code)
      field().dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
      await flushPromises()
    }

    it('opens the device of an exact hit', async () => {
      api.lookup.mockResolvedValue({ kind: 'asset', assets: [asset(1)], models: [] })
      const { router } = await show(GlobalScan)
      await scan('  NB-001 ')
      expect(api.lookup).toHaveBeenCalledWith('NB-001')
      expect(router.currentRoute.value.fullPath).toBe(`/inventory/assets/${ID(1)}`)
      expect(field().value).toBe('')
    })

    it('lists the devices of a model', async () => {
      api.lookup.mockResolvedValue({ kind: 'model', assets: [], models: [model as never] })
      const { router } = await show(GlobalScan)
      await scan('5099206')
      expect(router.currentRoute.value.fullPath).toBe(`/inventory/assets?model=${ID(91)}`)
    })

    it('lets the user pick among several hits', async () => {
      api.lookup.mockResolvedValue({
        kind: 'multiple',
        assets: [asset(1), asset(2)],
        models: [model as never],
      })
      const { router } = await show(GlobalScan)
      await scan('SN')
      expect(pageText()).toContain('3 matches for “SN”')
      const rows = [...document.body.querySelectorAll('.n-list-item')]
      expect(rows.map((r) => r.querySelector('.mono')?.textContent)).toEqual([
        'NB-001',
        'NB-002',
        '5099206',
      ])
      await click(rows[1]!)
      expect(router.currentRoute.value.fullPath).toBe(`/inventory/assets/${ID(2)}`)
    })

    it('says when nothing matches', async () => {
      api.lookup.mockResolvedValue({ kind: 'none', assets: [], models: [] })
      const { router } = await show(GlobalScan)
      await scan('XYZ-404')
      expect(pageText()).toContain('No match for “XYZ-404”')
      expect(router.currentRoute.value.fullPath).toBe('/')
    })

    it('says why the lookup failed and keeps the code for another try', async () => {
      api.lookup.mockRejectedValue(new ApiError(0, 'Argus is not reachable.'))
      const { router } = await show(GlobalScan)
      await scan('NB-001')
      expect(pageText()).toContain('Argus is not reachable.')
      expect(field().value).toBe('NB-001')
      expect(router.currentRoute.value.fullPath).toBe('/')
    })

    it('ignores an empty field', async () => {
      await show(GlobalScan)
      await scan('   ')
      expect(api.lookup).not.toHaveBeenCalled()
    })

    it('takes a scan anywhere on the page', async () => {
      api.lookup.mockResolvedValue({ kind: 'asset', assets: [asset(1)], models: [] })
      const { router } = await show(GlobalScan)
      for (const key of [...'NB-001', 'Enter'])
        document.body.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true }))
      await flushPromises()
      expect(api.lookup).toHaveBeenCalledWith('NB-001')
      expect(router.currentRoute.value.fullPath).toBe(`/inventory/assets/${ID(1)}`)
    })
  })

  describe('user menu', () => {
    afterEach(() => setLocale('en'))

    async function menu(user = makeUser({ display_name: 'Jane Doe' })) {
      const result = await show(UserMenu, { user })
      await click(document.body.querySelector('button.user')!)
      return result
    }
    const option = (label: string) =>
      [...document.body.querySelectorAll<HTMLElement>('.n-dropdown-option-body')].find((o) =>
        o.textContent?.trim().startsWith(label),
      )

    it('shows the initials and name', async () => {
      await menu()
      expect(document.body.querySelector('.avatar')?.textContent).toBe('JD')
      expect(document.body.querySelector('button.user')?.textContent).toContain('Jane Doe')
    })

    it('leads to the profile pages', async () => {
      const { router } = await menu()
      await click(option('Sign-in & security')!)
      expect(router.currentRoute.value.name).toBe('profile-security')
    })

    it('offers the Django admin to IT only', async () => {
      await menu()
      expect(option('Django admin')).toBeUndefined()
      unmount?.()
      document.body.innerHTML = ''
      const open = vi.spyOn(window, 'open').mockReturnValue(null)
      await menu(makeUser({ display_name: 'Ian IT', is_it_staff: true }))
      await click(option('Django admin')!)
      expect(open).toHaveBeenCalledWith('/admin/', '_blank')
      open.mockRestore()
    })

    it('opens the help in the interface language, IT staff in the IT area', async () => {
      const open = vi.spyOn(window, 'open').mockReturnValue(null)
      await menu()
      await click(option('Help')!)
      expect(open).toHaveBeenLastCalledWith('/docs/en/employees/', '_blank')
      unmount?.()
      document.body.innerHTML = ''
      setLocale('de')
      await menu(makeUser({ display_name: 'Ian IT', is_it_staff: true }))
      await click(option('Hilfe')!)
      expect(open).toHaveBeenLastCalledWith('/docs/de/it/', '_blank')
      open.mockRestore()
    })

    it('switches the language and stores it with the user', async () => {
      api.updatePreferences.mockResolvedValue(makeUser({ language: 'de' }))
      await menu()
      expect(option('English')?.textContent).toContain('✓')
      await click(option('Deutsch')!)
      expect(api.updatePreferences).toHaveBeenCalledWith({ language: 'de' })
      expect(document.documentElement.lang).toBe('de')
    })

    it('switches the theme, Solarized included, and stores it with the user', async () => {
      api.updatePreferences.mockResolvedValue(makeUser({ theme: 'solarized' }))
      await menu()
      expect(option('System')?.textContent).toContain('✓')
      await click(option('Solarized')!)
      expect(api.updatePreferences).toHaveBeenCalledWith({ theme: 'solarized' })
      expect(document.documentElement.dataset.theme).toBe('solarized')
      useTheme().mode.value = 'system'
    })

    it('leads to the appearance settings', async () => {
      const { router } = await menu()
      await click(option('Appearance')!)
      expect(router.currentRoute.value.name).toBe('profile-appearance')
    })

    it('signs out and goes to the login page', async () => {
      api.logout.mockResolvedValue()
      const { router } = await menu()
      await click(option('Sign out')!)
      expect(api.logout).toHaveBeenCalledOnce()
      expect(router.currentRoute.value.name).toBe('login')
    })
  })
})
