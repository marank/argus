import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Schemas } from '@/api/types'
import AppSidebar from '@/components/layout/AppSidebar.vue'

import { makeUser } from './helpers'
import { click } from './dom'
import { ALL_PERMISSIONS, mountView } from './layoutHelpers'

const menuCounts = vi.hoisted(() => vi.fn<() => Promise<Schemas['MenuCountsOut']>>())
vi.mock('@/api/requests', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/requests')>()),
  portalApi: { menuCounts },
}))

const COUNTS: Schemas['MenuCountsOut'] = {
  requests: 0,
  approvals: 0,
  issues: 0,
  issues_updated: false,
}

const itStaff = (fields: Partial<Schemas['CurrentUserOut']> = {}) =>
  makeUser({ is_it_staff: true, permissions: ALL_PERMISSIONS, ...fields })

/** Menu entries by section heading ('' for entries without one), as shown. */
function menu() {
  const result: Record<string, string[]> = {}
  let section = ''
  for (const node of document.body.querySelectorAll('.n-menu-item-group-title, .menu-text')) {
    if (node.classList.contains('menu-text')) (result[section] ??= []).push(node.textContent!)
    else section = node.textContent!.trim()
  }
  return result
}
const entries = () => Object.values(menu()).flat()
const entry = (label: string) =>
  [...document.body.querySelectorAll('.menu-link')].find(
    (a) => a.querySelector('.menu-text')?.textContent === label,
  )!

describe('sidebar', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    menuCounts.mockReset()
    menuCounts.mockResolvedValue(COUNTS)
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    localStorage.clear()
  })

  async function sidebar(
    options: {
      user?: Schemas['CurrentUserOut']
      flags?: Record<string, boolean>
      path?: string
      collapsed?: boolean
    } = {},
  ) {
    const result = await mountView(AppSidebar, {
      user: options.user ?? makeUser(),
      flags: options.flags,
      path: options.path,
      props: { collapsed: options.collapsed ?? false },
    })
    unmount = () => result.wrapper.unmount()
    return result
  }

  describe('entries', () => {
    it('shows employees the dashboard and self-service only', async () => {
      await sidebar()
      expect(menu()).toEqual({
        '': ['Dashboard'],
        'Self-service': ['New request', 'My requests', 'My devices', 'My software', 'My reports'],
      })
    })

    it('adds approvals for approvers', async () => {
      await sidebar({ user: makeUser({ is_approver: true }) })
      expect(menu()['Self-service']).toContain('Approvals')
    })

    it('shows IT the areas their roles allow', async () => {
      await sidebar({ user: itStaff({ permissions: { requests: 'write', assets: 'read' } }) })
      expect(menu()['IT operations']).toEqual(['Requests', 'Calendar', 'Devices', 'Service log'])
      // Sections without a single readable entry disappear.
      expect(menu()['Procurement']).toBeUndefined()
      expect(menu()['Master data']).toBeUndefined()
      expect(menu()['Administration']).toBeUndefined()
    })

    it('leaves out entries of switched-off modules', async () => {
      await sidebar({
        user: itStaff(),
        flags: { licenses: false, calendar: false, procurement: false },
      })
      const shown = entries()
      for (const label of ['My software', 'Licenses', 'Calendar', 'Demand', 'Purchase orders'])
        expect(shown).not.toContain(label)
      expect(menu()['Procurement']).toBeUndefined()
      expect(shown).toContain('Consumables')
    })

    it('offers administrators the settings and roles', async () => {
      await sidebar({ user: itStaff({ is_superuser: true }) })
      expect(menu()['Administration']).toEqual(['Settings'])
      expect(menu()['Master data']).toContain('Roles')
      expect(entry('Settings').getAttribute('href')).toBe('/settings')
    })

    it('keeps roles from IT members who are not administrators', async () => {
      await sidebar({ user: itStaff() })
      expect(menu()['Master data']).not.toContain('Roles')
      expect(menu()['Master data']).toContain('Employees')
    })

    it('links each entry to its page', async () => {
      await sidebar({ user: itStaff() })
      expect(entry('Purchase orders').getAttribute('href')).toBe('/procurement/orders')
      expect(entry('My reports').getAttribute('href')).toBe('/portal/issues')
    })

    it('highlights the entry of the current page', async () => {
      await sidebar({ user: itStaff(), path: '/inventory/licenses' })
      const selected = document.body.querySelector('.n-menu-item-content--selected .menu-text')
      expect(selected?.textContent).toBe('Licenses')
    })
  })

  describe('counts', () => {
    it('shows open requests and marks waiting approvals and changed reports', async () => {
      menuCounts.mockResolvedValue({ requests: 3, approvals: 2, issues: 0, issues_updated: true })
      await sidebar({ user: makeUser({ is_approver: true }) })
      const badge = (label: string) => entry(label).querySelector('.menu-badge')
      expect(badge('My requests')?.textContent).toBe('3')
      expect(badge('My requests')?.classList.contains('due')).toBe(false)
      expect(badge('Approvals')?.textContent).toBe('2')
      expect(badge('Approvals')?.classList.contains('due')).toBe(true)
      // A resolved report leaves no count, but its update still shows.
      expect(badge('My reports')?.textContent).toBe('!')
      expect(badge('My devices')).toBeNull()
    })

    it('marks waiting entries with a dot while collapsed', async () => {
      menuCounts.mockResolvedValue({ ...COUNTS, approvals: 1 })
      await sidebar({ user: makeUser({ is_approver: true }), collapsed: true })
      expect(document.body.querySelectorAll('.icon-dot')).toHaveLength(1)
    })

    it('refreshes them on every page change', async () => {
      const { router } = await sidebar()
      expect(menuCounts).toHaveBeenCalledOnce()
      await router.push('/portal/requests')
      expect(menuCounts).toHaveBeenCalledTimes(2)
    })
  })

  describe('folding', () => {
    const toggle = (label: string) =>
      [...document.body.querySelectorAll<HTMLButtonElement>('.section-toggle')].find(
        (b) => b.textContent?.trim() === label,
      )!
    const folded = () =>
      [...document.body.querySelectorAll('.folded .menu-text')].map((n) => n.textContent)

    it('folds a section away and remembers it', async () => {
      await sidebar({ user: itStaff() })
      await click(toggle('Procurement'))
      expect(toggle('Procurement').getAttribute('aria-expanded')).toBe('false')
      expect(folded()).toEqual(['Demand', 'Purchase orders'])
      expect(JSON.parse(localStorage.getItem('argus.sidebar-folded')!)).toEqual(['procurement'])
      await click(toggle('Procurement'))
      expect(folded()).toEqual([])
    })

    it('opens the folded section of the current page', async () => {
      localStorage.setItem('argus.sidebar-folded', JSON.stringify(['procurement', 'masterdata']))
      await sidebar({ user: itStaff(), path: '/procurement/needs' })
      expect(toggle('Procurement').getAttribute('aria-expanded')).toBe('true')
      expect(toggle('Master data').getAttribute('aria-expanded')).toBe('false')
    })

    it('does not fold for employees, who see a single section', async () => {
      await sidebar()
      expect(document.body.querySelector('.section-toggle')).toBeNull()
    })
  })
})
