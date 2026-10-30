import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Schemas } from '@/api/types'
import { defaultLayout, WIDGETS } from '@/components/dashboard/widgets'
import DashboardView from '@/views/DashboardView.vue'

import { makeUser } from './helpers'
import { click, hasButton, typeInto } from './dom'
import { ALL_PERMISSIONS, link, mountView, pageText } from './layoutHelpers'

type Widget = Schemas['DashboardWidgetOut']

const api = vi.hoisted(() => ({
  it: vi.fn<() => Promise<unknown>>(),
  me: vi.fn<() => Promise<unknown>>(),
  updatePreferences: vi.fn<(data: Record<string, unknown>) => Promise<unknown>>(),
}))

vi.mock('@/api/dashboard', () => ({
  dashboardApi: {
    it: api.it,
    me: api.me,
    // The widgets' own lists; empty is enough for the layout.
    myTasks: async () => ({ requests: [], issues: [], requests_total: 0, issues_total: 0 }),
    overdueReturns: async () => [],
    teamLoad: async () => ({ people: [], unassigned_requests: 0, unassigned_issues: 0 }),
    requestTrend: async () => [],
    upcoming: async () => [],
    dueReturns: async () => [],
    expiring: async () => [],
    lowStock: async () => [],
    openOrders: async () => [],
    waitingRequests: async () => [],
  },
}))
vi.mock('@/api/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/auth')>()),
  authApi: { updatePreferences: api.updatePreferences },
}))

function overview(fields: Partial<Schemas['ITOverviewOut']> = {}): Schemas['ITOverviewOut'] {
  return {
    asset_status: { in_stock: 4, in_use: 6 },
    issues_mine: 1,
    licenses_expiring: 0,
    low_consumables: 2,
    open_issues: 3,
    orders_in_transit: 1,
    orders_to_place: 0,
    recent_events: [],
    requests_mine: 5,
    requests_my_teams: 7,
    requests_overdue: 0,
    requests_ready: 2,
    requests_submitted: 3,
    requests_to_prepare: 4,
    requests_unassigned: 1,
    warranty_expiring: 0,
    ...fields,
  }
}

const itStaff = (fields: Partial<Schemas['CurrentUserOut']> = {}) =>
  makeUser({ first_name: 'Jane', is_it_staff: true, permissions: ALL_PERMISSIONS, ...fields })

/** The default layout with some widgets changed. */
function layoutWith(changes: Record<string, Partial<Widget>>): Widget[] {
  return defaultLayout(WIDGETS).map((w) => ({ ...w, ...changes[w.id] }))
}

/** The edit bar of the widget titled `title`. */
function editBar(title: string) {
  const bar = [...document.body.querySelectorAll('.edit-bar')].find(
    (b) => b.querySelector('.name')?.textContent?.trim() === title,
  )
  if (!bar) throw new Error(`no widget "${title}" in the editor`)
  return {
    button: (label: string) =>
      [...bar.querySelectorAll('button')].find((b) => b.title === label) as HTMLButtonElement,
  }
}

const widgetNames = () =>
  [...document.body.querySelectorAll('.edit-bar .name')].map((n) => n.textContent?.trim())

/** The layout the last save sent. */
function savedLayout(): Widget[] {
  const call = api.updatePreferences.mock.calls.at(-1)![0] as {
    dashboard_settings: { widgets: Widget[] }
  }
  return call.dashboard_settings.widgets
}

describe('IT dashboard', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
    api.it.mockResolvedValue(overview())
    api.updatePreferences.mockImplementation(async (data) => itStaff(data))
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.useRealTimers()
  })

  async function dashboard(
    options: { user?: Schemas['CurrentUserOut']; flags?: Record<string, boolean> } = {},
  ) {
    const result = await mountView(DashboardView, { user: options.user ?? itStaff(), ...options })
    unmount = () => result.wrapper.unmount()
    return result
  }

  async function edit() {
    await click('Customize dashboard')
  }

  describe('showing', () => {
    it('greets by first name and shows the default panels and widgets', async () => {
      await dashboard()
      const text = pageText()
      expect(text).toContain('Welcome, Jane')
      for (const title of [
        'My work',
        'Procurement & stock',
        'Deadlines & reports',
        'Devices by status',
        'Hand-outs (due and next 7 days)',
        'Recent activity',
      ])
        expect(text).toContain(title)
      // Optional widgets wait in the widget list.
      expect(text).not.toContain('Notes')
    })

    it('shows the figures with links to the matching lists', async () => {
      await dashboard()
      const toConfirm = link('To confirm')
      expect(toConfirm.textContent).toContain('3')
      expect(toConfirm.getAttribute('href')).toBe('/requests?status=submitted')
      expect(link('Unassigned').getAttribute('href')).toBe('/requests?assigned=nobody')
      expect(link('Consumables below minimum').getAttribute('href')).toBe(
        '/inventory/consumables?below_minimum=1',
      )
    })

    it('names the warning period of the site rules on the deadline cards', async () => {
      await dashboard()
      expect(pageText()).toContain('License ends ≤ 60 days')
      expect(pageText()).toContain('Warranty ends ≤ 60 days')
    })

    it('leaves out widgets and cards of areas the user may not read', async () => {
      await dashboard({ user: itStaff({ permissions: { requests: 'read' } }) })
      const text = pageText()
      expect(text).toContain('Assigned to me')
      expect(text).toContain('To confirm')
      expect(text).not.toContain('Reports with me')
      // Every card of these panels needs another area.
      expect(text).not.toContain('Procurement & stock')
      expect(text).not.toContain('Deadlines & reports')
      expect(text).not.toContain('Devices by status')
      expect(text).not.toContain('Recent activity')
    })

    it('leaves out cards and panels of switched-off modules', async () => {
      await dashboard({ flags: { procurement: false, consumables: false, issues: false } })
      const text = pageText()
      expect(text).not.toContain('Procurement & stock')
      expect(text).not.toContain('Reports with me')
      expect(text).not.toContain('Open problem reports')
      expect(text).toContain('License ends')
    })

    it('leaves out a panel whose cards are all hidden', async () => {
      const hidden = { hidden_cards: ['orders_to_place', 'orders_in_transit', 'below_minimum'] }
      await dashboard({
        user: itStaff({ dashboard_settings: { widgets: layoutWith({ stock: hidden }) } }),
      })
      expect(pageText()).not.toContain('Procurement & stock')
      await edit()
      // While editing it stays, so the cards can be shown again.
      expect(widgetNames()).toContain('Procurement & stock')
    })

    it('says so when every widget is hidden', async () => {
      const widgets = defaultLayout(WIDGETS).map((w) => ({ ...w, visible: false }))
      await dashboard({ user: itStaff({ dashboard_settings: { widgets } }) })
      expect(pageText()).toContain('Your dashboard is empty')
    })

    it('shows employees their own overview without the editor', async () => {
      api.me.mockResolvedValue({
        open_requests: 2,
        assigned_assets: 3,
        ready_for_pickup: [],
        returns_due: [],
      })
      await dashboard({ user: makeUser({ first_name: 'Paul' }) })
      expect(api.it).not.toHaveBeenCalled()
      expect(pageText()).toContain('Your requests and devices at a glance.')
      expect(link('Open requests').getAttribute('href')).toBe('/portal/requests')
      expect(link('Assigned devices').textContent).toContain('3')
      expect(hasButton('Customize dashboard')).toBe(false)
    })

    it('reminds employees of returns, the overdue ones in red', async () => {
      api.me.mockResolvedValue({
        open_requests: 2,
        assigned_assets: 3,
        ready_for_pickup: [],
        returns_due: [
          { id: 'r1', number: 'R-1', title: 'Headset', end_date: '2020-01-31' },
          { id: 'r2', number: 'R-2', title: 'Beamer', end_date: '2099-01-31' },
        ],
      })
      await dashboard({ user: makeUser({ first_name: 'Paul' }) })
      expect(link('R-1').textContent).toContain('Return overdue since')
      expect(link('R-1').querySelector('strong.late')).not.toBeNull()
      expect(link('R-2').textContent).toContain('Return by')
      expect(link('R-2').querySelector('strong.late')).toBeNull()
      expect(link('R-1').getAttribute('href')).toBe('/portal/requests/r1')
    })
  })

  describe('editing', () => {
    it('saves no layout when nothing changed', async () => {
      await dashboard()
      await edit()
      expect(pageText()).toContain('Editing')
      await click('Done')
      expect(api.updatePreferences).toHaveBeenCalledWith({ dashboard_settings: { widgets: [] } })
      expect(pageText()).not.toContain('Editing')
    })

    it('hides a widget and saves the whole layout', async () => {
      await dashboard()
      await edit()
      await click(editBar('Recent activity').button('Remove'))
      expect(widgetNames()).not.toContain('Recent activity')
      await click('Done')
      expect(savedLayout()).toEqual(layoutWith({ activity: { visible: false } }))
      expect(pageText()).not.toContain('Recent activity')
    })

    it('changes the width of a widget', async () => {
      await dashboard()
      await edit()
      await click(editBar('Recent activity').button('Size'))
      await click('Third')
      await click('Done')
      expect(savedLayout().find((w) => w.id === 'activity')).toMatchObject({ size: 'small' })
    })

    it('changes the height of a widget', async () => {
      await dashboard()
      await edit()
      await click(editBar('Recent activity').button('Size'))
      await click('Tall')
      await click('Done')
      expect(savedLayout().find((w) => w.id === 'activity')).toMatchObject({ height: 'large' })
    })

    it('moves a widget back and forward', async () => {
      await dashboard()
      await edit()
      expect(editBar('My work').button('Move forward').disabled).toBe(true)
      await click(editBar('My work').button('Move back'))
      expect(widgetNames().slice(0, 2)).toEqual(['Requests', 'My work'])
      await click(editBar('Recent activity').button('Move forward'))
      await click('Done')
      expect(
        savedLayout()
          .map((w) => w.id)
          .slice(0, 7),
      ).toEqual(['requests', 'mine', 'stock', 'attention', 'asset_status', 'activity', 'upcoming'])
    })

    it('hides a key figure of a panel', async () => {
      await dashboard()
      await edit()
      const card = [...document.body.querySelectorAll('.card-edit')].find((c) =>
        c.textContent?.includes('To confirm'),
      )!
      await click(card.querySelector('button[title="Hide"]')!)
      await click('Done')
      expect(savedLayout().find((w) => w.id === 'requests')?.hidden_cards).toEqual(['to_confirm'])
      expect(pageText()).not.toContain('To confirm')
    })

    it('reorders the key figures of a panel, storing the default order as none', async () => {
      await dashboard()
      await edit()
      const card = (label: string) =>
        [...document.body.querySelectorAll('.card-edit')].find((c) =>
          c.textContent?.includes(label),
        )!
      await click(card('To confirm').querySelector('button[title="Move back"]')!)
      const labels = [...document.body.querySelectorAll('.card-edit .eyebrow')]
        .map((l) => l.textContent?.trim())
        .slice(4, 8)
      expect(labels).toEqual(['To prepare', 'To confirm', 'Ready for pickup', 'Overdue returns'])
      await click('Done')
      expect(savedLayout().find((w) => w.id === 'requests')?.card_order).toEqual([
        'to_prepare',
        'to_confirm',
        'ready',
        'overdue',
      ])

      await edit()
      await click(card('To confirm').querySelector('button[title="Move forward"]')!)
      await click('Done')
      expect(savedLayout()).toEqual([])
    })

    it('discards the changes on cancel', async () => {
      await dashboard()
      await edit()
      await click(editBar('Recent activity').button('Remove'))
      await click('Cancel')
      expect(api.updatePreferences).not.toHaveBeenCalled()
      expect(pageText()).toContain('Recent activity')
    })

    it('restores the default layout, which is stored as none', async () => {
      const widgets = layoutWith({ activity: { visible: false }, mine: { size: 'small' } })
      await dashboard({ user: itStaff({ dashboard_settings: { widgets } }) })
      await edit()
      await click('Restore default')
      expect(widgetNames()).toContain('Recent activity')
      await click('Done')
      expect(savedLayout()).toEqual([])
    })

    it('keeps editing and says so when saving fails', async () => {
      api.updatePreferences.mockRejectedValue(new Error('offline'))
      await dashboard()
      await edit()
      await click(editBar('Recent activity').button('Remove'))
      await click('Done')
      expect(pageText()).toContain('Editing')
      expect(widgetNames()).not.toContain('Recent activity')
    })
  })

  describe('widget list', () => {
    const entry = (title: string) =>
      [...document.body.querySelectorAll('.picker-list li')].find(
        (li) => li.querySelector('strong')?.textContent?.trim() === title,
      )

    it('adds an optional widget at the end', async () => {
      await dashboard()
      await edit()
      await click('Add widget')
      await click(entry('Notes')!.querySelector('button')!)
      expect(widgetNames().at(-1)).toBe('Notes')
      await click('Done')
      const notes = savedLayout().at(-1)!
      expect(notes).toMatchObject({ id: 'notes', widget: null, visible: true })
    })

    it('offers a widget allowing several once more while it is on the dashboard', async () => {
      await dashboard()
      await edit()
      await click('Add widget')
      const upcoming = entry('Upcoming hand-outs')!
      expect(upcoming.textContent).toContain('1× on the dashboard')
      expect(upcoming.textContent).toContain('Multiple')
      await click(upcoming.querySelector('button')!)
      expect(widgetNames().filter((n) => n === 'Upcoming hand-outs')).toHaveLength(2)
      await click('Done')
      const copy = savedLayout().at(-1)!
      expect(copy).toMatchObject({ widget: 'upcoming', visible: true, size: 'medium' })
      expect(copy.id).toMatch(/^upcoming~/)
    })

    it('offers a hidden widget again instead of another one', async () => {
      await dashboard()
      await edit()
      await click(editBar('Upcoming hand-outs').button('Remove'))
      await click('Add widget')
      expect(entry('Upcoming hand-outs')!.querySelector('button')!.textContent?.trim()).toBe('Add')
      expect(entry('Recent activity')).toBeUndefined()
    })

    it('does not offer widgets of areas the user may not read or of switched-off modules', async () => {
      const { procurement: _procurement, ...withoutProcurement } = ALL_PERMISSIONS
      await dashboard({
        user: itStaff({ permissions: withoutProcurement }),
        flags: { consumables: false },
      })
      await edit()
      await click('Add widget')
      expect(entry('My tasks')).toBeDefined()
      expect(entry('Open orders')).toBeUndefined()
      expect(entry('Consumables running low')).toBeUndefined()
    })
  })

  describe('further instances', () => {
    const copy: Widget = {
      id: 'upcoming~abc123',
      widget: 'upcoming',
      visible: true,
      size: 'medium',
      height: 'auto',
      hidden_cards: [],
      card_order: [],
      options: {},
    }

    it('can be renamed, and show their name', async () => {
      await dashboard({
        user: itStaff({ dashboard_settings: { widgets: [...layoutWith({}), copy] } }),
      })
      await edit()
      const bars = [...document.body.querySelectorAll('.edit-bar')].filter((b) =>
        b.textContent?.includes('Upcoming hand-outs'),
      )
      // Every instance of a widget allowing several can be named, single ones cannot.
      expect(bars.every((b) => b.querySelector('button[title="Custom title"]'))).toBe(true)
      expect(editBar('Recent activity').button('Custom title')).toBeUndefined()

      await click(bars.at(-1)!.querySelector('button[title="Custom title"]')!)
      await typeInto(document.body.querySelector('.rename input'), 'Counter')
      expect(widgetNames()).toContain('Counter')
      await click('Done')
      expect(savedLayout().find((w) => w.id === copy.id)?.options).toEqual({ title: 'Counter' })
    })

    it('go away entirely when removed', async () => {
      await dashboard({
        user: itStaff({ dashboard_settings: { widgets: [...layoutWith({}), copy] } }),
      })
      await edit()
      const bars = [...document.body.querySelectorAll('.edit-bar')].filter((b) =>
        b.textContent?.includes('Upcoming hand-outs'),
      )
      await click(bars.at(-1)!.querySelector('button[title="Remove"]')!)
      await click('Done')
      // Without the copy what is left is the default layout, stored as none.
      expect(savedLayout()).toEqual([])
    })
  })

  it('saves a setting changed in a widget right away outside the editor', async () => {
    const widgets = layoutWith({ request_trend: { visible: true } })
    await dashboard({ user: itStaff({ dashboard_settings: { widgets } }) })
    await click('Show as table')
    expect(savedLayout().find((w) => w.id === 'request_trend')?.options).toEqual({
      as_table: true,
    })
    expect(api.updatePreferences).toHaveBeenCalledOnce()
    await flushPromises()
  })
})
