import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Component } from 'vue'

import type { Schemas } from '@/api/types'
import ActivityWidget from '@/components/dashboard/widgets/ActivityWidget.vue'
import AssetStatusWidget from '@/components/dashboard/widgets/AssetStatusWidget.vue'
import DueReturnsWidget from '@/components/dashboard/widgets/DueReturnsWidget.vue'
import ExpiringWidget from '@/components/dashboard/widgets/ExpiringWidget.vue'
import LowStockWidget from '@/components/dashboard/widgets/LowStockWidget.vue'
import MyTasksWidget from '@/components/dashboard/widgets/MyTasksWidget.vue'
import NotesWidget from '@/components/dashboard/widgets/NotesWidget.vue'
import OpenOrdersWidget from '@/components/dashboard/widgets/OpenOrdersWidget.vue'
import RequestTrendWidget from '@/components/dashboard/widgets/RequestTrendWidget.vue'
import ShortcutsWidget from '@/components/dashboard/widgets/ShortcutsWidget.vue'
import TeamLoadWidget from '@/components/dashboard/widgets/TeamLoadWidget.vue'
import UpcomingWidget from '@/components/dashboard/widgets/UpcomingWidget.vue'
import WaitingRequestsWidget from '@/components/dashboard/widgets/WaitingRequestsWidget.vue'

import { makeUser } from './helpers'
import { click, typeInto } from './dom'
import { ALL_PERMISSIONS, link, mountView, pageText } from './layoutHelpers'

const api = vi.hoisted(() => ({
  requestTrend: vi.fn<() => Promise<Schemas['TrendWeekOut'][]>>(),
  teamLoad: vi.fn<() => Promise<Schemas['TeamLoadOut']>>(),
  myTasks: vi.fn<() => Promise<Schemas['MyTasksOut']>>(),
  upcoming: vi.fn<(days: number) => Promise<Schemas['UpcomingOut'][]>>(),
  lowStock: vi.fn<() => Promise<Schemas['LowStockOut'][]>>(),
  expiring: vi.fn<() => Promise<Schemas['ExpiringOut'][]>>(),
  openOrders: vi.fn<() => Promise<Schemas['OpenOrderOut'][]>>(),
  waitingRequests: vi.fn<() => Promise<Schemas['WaitingRequestOut'][]>>(),
  dueReturns: vi.fn<(days: number) => Promise<Schemas['DueReturnOut'][]>>(),
}))
vi.mock('@/api/dashboard', () => ({ dashboardApi: api }))

const ID = (n: number) => `0192f0c4-6a3e-7b4d-9a1e-${String(n).padStart(12, '0')}`
const person = (n: number, name: string): Schemas['UserRefOut'] => ({
  id: ID(n),
  username: name.toLowerCase(),
  display_name: name,
})
const model: Schemas['AssetModelRefOut'] = {
  id: ID(90),
  name: 'Latitude 5550',
  designation: '',
  full_name: 'Dell Latitude 5550',
  tracking: 'serialized',
}
const NO_DATA = {} as Schemas['ITOverviewOut']

const itStaff = (permissions: Schemas['CurrentUserOut']['permissions'] = ALL_PERMISSIONS) =>
  makeUser({ is_it_staff: true, permissions })

/** Mounts a widget as the dashboard does; `saved` receives what it emits as `update:options`. */
async function widget(
  component: Component,
  options: {
    data?: Schemas['ITOverviewOut']
    stored?: Record<string, unknown>
    flags?: Record<string, boolean>
    user?: Schemas['CurrentUserOut']
    title?: string
  } = {},
) {
  const saved = vi.fn<(options: Record<string, unknown>) => void>()
  const result = await mountView(component, {
    user: options.user ?? itStaff(),
    flags: options.flags,
    props: {
      data: options.data ?? NO_DATA,
      options: options.stored ?? {},
      title: options.title,
      'onUpdate:options': saved,
    },
  })
  return { ...result, saved }
}

describe('dashboard widgets', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.useRealTimers()
  })

  async function show(...args: Parameters<typeof widget>) {
    const result = await widget(...args)
    unmount = () => result.wrapper.unmount()
    return result
  }

  describe('requests per week', () => {
    const weeks: Schemas['TrendWeekOut'][] = [
      { week_start: '2025-12-29', created: 4, completed: 1 },
      { week_start: '2026-01-05', created: 3, completed: 4 },
    ]

    it('sums up new and completed requests', async () => {
      api.requestTrend.mockResolvedValue(weeks)
      await show(RequestTrendWidget)
      const legend = document.body.querySelector('.legend')!.textContent!
      expect(legend).toMatch(/New\s*7/)
      expect(legend).toMatch(/Completed\s*5/)
    })

    it('describes each week by its ISO calendar week', async () => {
      api.requestTrend.mockResolvedValue(weeks)
      await show(RequestTrendWidget)
      const bands = [...document.body.querySelectorAll('.band')].map((b) =>
        b.getAttribute('aria-label'),
      )
      // 29 Dec 2025 starts week 1 of 2026: its Thursday is 1 January.
      expect(bands[0]).toMatch(/^CW 1 \(.*\): New 4, Completed 1$/)
      expect(bands[1]).toMatch(/^CW 2 \(.*\): New 3, Completed 4$/)
    })

    it('lists the weeks as table, newest first, and keeps that choice', async () => {
      api.requestTrend.mockResolvedValue(weeks)
      const { saved } = await show(RequestTrendWidget)
      await click('Show as table')
      const rows = [...document.body.querySelectorAll('tbody tr')].map((r) =>
        [...r.querySelectorAll('td')].map((c) => c.textContent?.trim()),
      )
      expect(rows.map((r) => r.slice(1))).toEqual([
        ['3', '4'],
        ['4', '1'],
      ])
      expect(rows[0]![0]).toContain('CW 2')
      expect(saved).toHaveBeenCalledWith({ as_table: true })
    })

    it('scales the axis to a round number above the highest week', async () => {
      api.requestTrend.mockResolvedValue([{ week_start: '2026-01-05', created: 13, completed: 2 }])
      await show(RequestTrendWidget)
      const ticks = [...document.body.querySelectorAll('.axis span')].map((s) => s.textContent)
      expect(ticks).toEqual(['20', '10', '0'])
    })
  })

  describe('devices by status', () => {
    it('counts all devices and links each status to the filtered list', async () => {
      await show(AssetStatusWidget, {
        data: { asset_status: { in_stock: 4, in_use: 6, in_repair: 1 } } as never,
      })
      expect(pageText()).toContain('Σ 11')
      const inUse = link('In use')
      expect(inUse.textContent).toContain('6')
      expect(inUse.getAttribute('href')).toBe('/inventory/assets?status=in_use')
      expect(link('Lost').textContent).toContain('0')
    })
  })

  describe('team workload', () => {
    const load = (people: Schemas['TeamMemberLoadOut'][]): Schemas['TeamLoadOut'] => ({
      people,
      unassigned_requests: 2,
      unassigned_issues: 3,
    })

    it('adds up requests and reports per person', async () => {
      api.teamLoad.mockResolvedValue(load([{ user: person(1, 'Anna'), requests: 4, issues: 2 }]))
      await show(TeamLoadWidget)
      const row = document.body.querySelector('.row')!
      expect(row.querySelector('.value')?.textContent).toBe('6')
      expect(row.textContent).toContain('4 req. · 2 rep.')
      expect(link('Unassigned').textContent).toContain('5')
      expect(link('Unassigned').getAttribute('href')).toBe('/requests?assigned=nobody')
    })

    it('counts requests only while problem reports are switched off', async () => {
      api.teamLoad.mockResolvedValue(load([{ user: person(1, 'Anna'), requests: 4, issues: 2 }]))
      await show(TeamLoadWidget, { flags: { issues: false } })
      expect(document.body.querySelector('.row .value')?.textContent).toBe('4')
      expect(pageText()).not.toContain('rep.')
      expect(link('Unassigned').textContent).toContain('2')
    })

    it('sums up the people beyond eight rows', async () => {
      const people = Array.from({ length: 10 }, (_, i) => ({
        user: person(i + 1, `Member ${i + 1}`),
        requests: 1,
        issues: 0,
      }))
      api.teamLoad.mockResolvedValue(load(people))
      await show(TeamLoadWidget)
      expect(document.body.querySelectorAll('.row')).toHaveLength(8)
      expect(pageText()).toContain('and 2 more')
    })
  })

  describe('my tasks', () => {
    const tasks = (fields: Partial<Schemas['MyTasksOut']> = {}): Schemas['MyTasksOut'] => ({
      requests: [
        {
          id: ID(1),
          number: 'REQ-2026-00042',
          title: 'Laptop for trainee',
          requester: person(5, 'Paul Wolf'),
          start_date: '2026-11-02',
          end_date: null,
          status: 'confirmed',
        },
      ],
      requests_total: 1,
      issues: [
        {
          id: ID(2),
          asset: {
            id: ID(3),
            inventory_number: 'NB-0815',
            name: '',
            model,
            serial_number: 'SN1',
            status: 'in_use',
          },
          created_at: '2026-10-28T09:00:00Z',
          description: 'Display flickers',
          kind: 'defect',
          reported_by: person(5, 'Paul Wolf'),
          status: 'open',
        },
      ],
      issues_total: 1,
      ...fields,
    })

    it('lists assigned requests and reports with links to them', async () => {
      api.myTasks.mockResolvedValue(tasks())
      await show(MyTasksWidget)
      expect(link('Requests (1)').getAttribute('href')).toBe('/requests?assigned=me')
      expect(link('REQ-2026-00042').getAttribute('href')).toBe(`/requests/${ID(1)}`)
      expect(link('Problem reports (1)').getAttribute('href')).toBe('/inventory/issues?assigned=me')
      expect(link('NB-0815').textContent).toContain('Dell Latitude 5550')
    })

    it('opens an assigned report on its own page', async () => {
      api.myTasks.mockResolvedValue(tasks())
      await show(MyTasksWidget)
      expect(link('NB-0815').getAttribute('href')).toBe(`/inventory/issues/${ID(2)}`)
    })

    it('leaves out reports while problem reports are switched off', async () => {
      api.myTasks.mockResolvedValue(tasks())
      await show(MyTasksWidget, { flags: { issues: false } })
      expect(pageText()).toContain('REQ-2026-00042')
      expect(pageText()).not.toContain('NB-0815')
    })

    it('says when nothing is assigned', async () => {
      api.myTasks.mockResolvedValue(
        tasks({ requests: [], issues: [], requests_total: 0, issues_total: 0 }),
      )
      await show(MyTasksWidget)
      expect(pageText()).toContain('No tasks are currently assigned to you.')
    })
  })

  describe('upcoming hand-outs', () => {
    // The hand-out days below are fixed; seen from this day the first is still ahead.
    beforeEach(() => {
      vi.useFakeTimers({ toFake: ['Date'] })
      vi.setSystemTime(new Date(2026, 9, 30, 12))
    })
    afterEach(() => vi.useRealTimers())

    const row: Schemas['UpcomingOut'] = {
      id: ID(7),
      number: 'REQ-2026-00007',
      title: 'Projector for training',
      requester: person(5, 'Paul Wolf'),
      start_date: '2026-11-03',
      pickup_at: null,
      status: 'ready',
    }

    it('asks for the stored period and links each request', async () => {
      api.upcoming.mockResolvedValue([row])
      await show(UpcomingWidget, { stored: { days: 14 } })
      expect(api.upcoming).toHaveBeenCalledWith(14)
      expect(pageText()).toContain('Hand-outs (due and next 14 days)')
      expect(link('REQ-2026-00007').getAttribute('href')).toBe(`/requests/${ID(7)}`)
      expect(link('REQ-2026-00007').textContent).toContain('Paul Wolf')
      expect(link('REQ-2026-00007').querySelector('.when')!.classList).not.toContain('overdue')
    })

    it('marks hand-outs whose day has passed as overdue', async () => {
      api.upcoming.mockResolvedValue([{ ...row, start_date: '2026-10-20' }])
      await show(UpcomingWidget)
      const when = link('REQ-2026-00007').querySelector('.when')!
      expect(when.classList).toContain('overdue')
      expect(when.getAttribute('title')).toContain('Hand-out overdue')
    })

    it('falls back to a week for a period it does not offer', async () => {
      api.upcoming.mockResolvedValue([])
      await show(UpcomingWidget, { stored: { days: 30 } })
      expect(api.upcoming).toHaveBeenCalledWith(7)
      expect(pageText()).toContain('No hand-outs scheduled.')
    })

    it('shows the name given to the instance instead of its own', async () => {
      api.upcoming.mockResolvedValue([])
      await show(UpcomingWidget, { title: 'Counter' })
      expect(pageText()).toContain('Counter')
      expect(pageText()).not.toContain('Upcoming hand-outs')
    })
  })

  describe('consumables running low', () => {
    const item: Schemas['LowStockOut'] = {
      id: ID(8),
      model: { ...model, full_name: 'HP 305 black' },
      location: { id: ID(9), name: 'Store room', full_name: 'HQ / Store room' },
      quantity: 1,
      min_quantity: 5,
    }

    it('shows stock against minimum with a link to the shortfall list', async () => {
      api.lowStock.mockResolvedValue([item])
      await show(LowStockWidget)
      const line = link('HP 305 black')
      expect(line.textContent).toContain('Store room')
      expect(line.querySelector('.stock')?.textContent?.trim()).toBe('1')
      expect(line.textContent).toContain('/ 5')
      expect(line.getAttribute('href')).toBe('/inventory/consumables?below_minimum=1')
      expect(link('Demand').getAttribute('href')).toBe('/procurement/needs')
    })

    it('offers the needs list only while procurement is on', async () => {
      api.lowStock.mockResolvedValue([item])
      await show(LowStockWidget, { flags: { procurement: false } })
      expect(() => link('Demand')).toThrow('no link "Demand"')
    })
  })

  describe('expiring licenses and warranties', () => {
    const items: Schemas['ExpiringOut'][] = [
      { kind: 'license', id: ID(10), label: 'Adobe CC', detail: '', ends_on: '2026-11-20' },
      { kind: 'warranty', id: ID(11), label: 'NB-0815', detail: 'Dell', ends_on: '2026-12-01' },
    ]

    it('links licenses and devices to their pages', async () => {
      api.expiring.mockResolvedValue(items)
      await show(ExpiringWidget)
      expect(link('Adobe CC').getAttribute('href')).toBe(`/inventory/licenses/${ID(10)}`)
      expect(link('NB-0815').getAttribute('href')).toBe(`/inventory/assets/${ID(11)}`)
    })

    it('leaves out licenses while the module is off', async () => {
      api.expiring.mockResolvedValue(items)
      await show(ExpiringWidget, { flags: { licenses: false } })
      expect(pageText()).not.toContain('Adobe CC')
      expect(pageText()).toContain('NB-0815')
    })
  })

  describe('shortcuts', () => {
    const shortcuts = () =>
      [...document.body.querySelectorAll('.shortcut')].map((a) => a.textContent?.trim())

    it('starts with the common pages, in menu order', async () => {
      await show(ShortcutsWidget)
      expect(shortcuts()).toEqual([
        'New request',
        'Requests',
        'Calendar',
        'Devices',
        'Purchase orders',
      ])
    })

    it('shows the pages picked, without those of switched-off modules', async () => {
      await show(ShortcutsWidget, {
        stored: { keys: ['orders', 'licenses', 'assets'] },
        flags: { procurement: false },
      })
      expect(shortcuts()).toEqual(['Devices', 'Licenses'])
    })

    it('stores the pages chosen', async () => {
      const { saved } = await show(ShortcutsWidget, { stored: { keys: ['assets'] } })
      await click('Choose pages')
      await click(document.body.querySelector('.choices .n-checkbox')!)
      expect(saved).toHaveBeenCalledWith({ keys: ['assets', 'portal-new'] })
    })

    it('offers only pages the user may open', async () => {
      await show(ShortcutsWidget, { user: itStaff({ requests: 'write', assets: 'write' }) })
      expect(shortcuts()).not.toContain('Purchase orders')
    })
  })

  describe('open orders', () => {
    const order = (n: number, fields: Partial<Schemas['OpenOrderOut']> = {}) => ({
      id: ID(n),
      number: `PO-2026-0000${n}`,
      supplier: { id: ID(50), name: 'Nordlicht' },
      status: 'ordered' as const,
      order_date: '2026-10-01',
      expected_date: null,
      ...fields,
    })

    it('marks orders past their expected delivery and links each order', async () => {
      vi.useFakeTimers({ toFake: ['Date'] })
      vi.setSystemTime(new Date(2026, 9, 30, 12))
      api.openOrders.mockResolvedValue([
        order(1, { expected_date: '2026-10-29' }),
        order(2, { expected_date: '2026-10-30' }),
        order(3, { supplier: null }),
      ])
      await show(OpenOrdersWidget)
      const late = (n: number) =>
        link(`PO-2026-0000${n}`).querySelector('.when')?.classList.contains('late')
      expect(late(1)).toBe(true)
      expect(late(2)).toBe(false)
      expect(link('PO-2026-00003').textContent).toContain('no date')
      expect(link('PO-2026-00003').textContent).toContain('—')
      expect(link('PO-2026-00001').getAttribute('href')).toBe(`/procurement/orders/${ID(1)}`)
    })
  })

  describe('waiting requests', () => {
    const waiting = (fields: Partial<Schemas['WaitingRequestOut']> = {}) => ({
      id: ID(20),
      number: 'REQ-2026-00020',
      title: 'Headset',
      requester: person(5, 'Paul Wolf'),
      assignee: null,
      created_at: '2026-10-20T08:00:00Z',
      start_date: '2026-11-02',
      ...fields,
    })

    it('names who has each request, or that nobody has', async () => {
      api.waitingRequests.mockResolvedValue([
        waiting(),
        waiting({ id: ID(21), number: 'REQ-2026-00021', assignee: person(6, 'Ian IT') }),
      ])
      await show(WaitingRequestsWidget)
      expect(link('REQ-2026-00020').querySelector('.assignee')?.textContent).toBe('Unassigned')
      expect(link('REQ-2026-00021').querySelector('.assignee')?.textContent).toBe('Ian IT')
      expect(link('REQ-2026-00020').getAttribute('href')).toBe(`/requests/${ID(20)}`)
    })

    it('keeps the choice of full dates', async () => {
      api.waitingRequests.mockResolvedValue([waiting()])
      const { saved } = await show(WaitingRequestsWidget, { stored: { days: 3 } })
      await click('Show full dates')
      expect(saved).toHaveBeenCalledWith({ days: 3, dates: 'full' })
      expect(link('REQ-2026-00020').querySelector('.when')?.classList.contains('full')).toBe(true)
    })
  })

  describe('returns due soon', () => {
    const due = (fields: Partial<Schemas['DueReturnOut']> = {}): Schemas['DueReturnOut'] => ({
      id: ID(30),
      number: 'REQ-2026-00030',
      title: 'Beamer',
      requester: person(5, 'Paul Wolf'),
      end_date: '2026-11-01',
      can_remind: true,
      reminded_at: null,
      reminded_by: null,
      ...fields,
    })

    it('looks three days ahead unless another period is stored', async () => {
      api.dueReturns.mockResolvedValue([])
      await show(DueReturnsWidget)
      expect(api.dueReturns).toHaveBeenCalledWith(3)
      expect(pageText()).toContain('No loans end in the next 3 days.')
    })

    it('cannot remind someone without an email address', async () => {
      api.dueReturns.mockResolvedValue([due({ can_remind: false })])
      await show(DueReturnsWidget, { stored: { days: 7 } })
      expect(api.dueReturns).toHaveBeenCalledWith(7)
      const remind = [...document.body.querySelectorAll('button')].find((b) =>
        b.textContent?.includes('Remind'),
      )!
      expect(remind.disabled).toBe(true)
      expect(remind.title).toBe('No email address on file')
      expect(link('REQ-2026-00030').getAttribute('href')).toBe(`/requests/${ID(30)}`)
    })
  })

  describe('notes', () => {
    it('saves the text once typing pauses', async () => {
      vi.useFakeTimers()
      const { saved } = await show(NotesWidget, {
        stored: { text: 'Call Paul', dates: 'full' },
        title: 'Desk',
      })
      expect(pageText()).toContain('Desk')
      const area = document.body.querySelector('textarea')!
      expect(area.value).toBe('Call Paul')
      await typeInto(area, 'Call Paul back')
      expect(pageText()).toContain('Saving …')
      expect(saved).not.toHaveBeenCalled()
      await vi.advanceTimersByTimeAsync(800)
      await flushPromises()
      // Other stored settings stay.
      expect(saved).toHaveBeenCalledWith({ text: 'Call Paul back', dates: 'full' })
      expect(pageText()).toContain('Saved')
    })
  })

  describe('recent activity', () => {
    const row = (overrides: Partial<Schemas['ActivityOut']>): Schemas['ActivityOut'] => ({
      id: ID(1),
      occurred_at: '2026-11-18T09:00:00Z',
      area: 'requests',
      kind: 'request_handed_out',
      subject_id: ID(2),
      subject_label: 'REQ-2026-0042 – Workshop',
      actor: person(3, 'Ian'),
      related_user: null,
      quantity: 3,
      detail: '',
      ...overrides,
    })

    it('shows a hand-out as one line linking to the request', async () => {
      const data = {
        ...NO_DATA,
        recent_events: [
          row({}),
          row({
            id: ID(4),
            area: 'assets',
            kind: 'asset_deleted',
            subject_id: null,
            subject_label: 'NB-0001',
            quantity: null,
          }),
        ],
      }
      await show(ActivityWidget, { data })
      const handOut = link('REQ-2026-0042')
      expect(handOut.textContent).toContain('Handed out · 3 items')
      expect(handOut.getAttribute('href')).toContain(ID(2))
      expect(pageText()).toContain('NB-0001')
      expect(() => link('NB-0001')).toThrow('no link')
      expect(link('Show all').getAttribute('href')).toBe('/activities')
    })
  })
})
