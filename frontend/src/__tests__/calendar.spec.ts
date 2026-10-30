import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import type { Schemas } from '@/api/types'
import { entryColor, entryLabel, entryRoute, isTentative } from '@/components/calendar/kinds'
import { i18n } from '@/i18n'
import { routes } from '@/router/routes'
import CalendarView from '@/views/calendar/CalendarView.vue'

import { makeUser } from './helpers'
import { click } from './dom'
import { ALL_PERMISSIONS, mountView } from './layoutHelpers'

type Entry = Schemas['CalendarEntryOut']

/** What the page hands FullCalendar, and the calendar API it calls back. */
const calendar = vi.hoisted(() => ({
  options: null as null | {
    events: (info: {
      start: Date
      end: Date
    }) => Promise<{ id: string; title: string; color: string; className?: string }[]>
    eventClick: (info: { event: { extendedProps: { entry: unknown } } }) => void
    initialView: string
  },
  api: {
    refetchEvents: vi.fn<() => void>(),
    changeView: vi.fn<(name: string) => void>(),
    prev: vi.fn<() => void>(),
    next: vi.fn<() => void>(),
    today: vi.fn<() => void>(),
  },
}))
vi.mock('@fullcalendar/vue3', async () => {
  const { defineComponent, h, watchEffect } = await import('vue')
  return {
    default: defineComponent({
      props: { options: { type: Object, required: true } },
      setup(props, { expose }) {
        expose({ getApi: () => calendar.api })
        watchEffect(() => (calendar.options = props.options as typeof calendar.options))
        return () => h('div', { class: 'calendar-stub' })
      },
    }),
  }
})

const entriesApi = vi.hoisted(() =>
  vi.fn<
    (start: string, end: string, kinds: string[], assigned?: string | null) => Promise<Entry[]>
  >(),
)
vi.mock('@/api/calendar', () => ({ calendarApi: { entries: entriesApi } }))

const ID = (n: number) => `0192f0c4-6a3e-7b4d-9a1e-${String(n).padStart(12, '0')}`

function entry(kind: Entry['kind'], fields: Partial<Entry> = {}): Entry {
  return {
    id: `${kind}-1`,
    kind,
    title: 'Paul Wolf',
    start: '2026-11-03',
    end: null,
    all_day: true,
    status: 'confirmed',
    overdue: false,
    due: null,
    details: [],
    link: {},
    ...fields,
  }
}

const MONTH = { start: new Date(2026, 9, 26), end: new Date(2026, 11, 7) }
const chips = () =>
  [...document.body.querySelectorAll<HTMLButtonElement>('.filters .chip')].map((c) => [
    c.textContent?.trim(),
    c.getAttribute('aria-pressed'),
  ])
const chip = (label: string) =>
  [...document.body.querySelectorAll<HTMLButtonElement>('.filters .chip')].find(
    (c) => c.textContent?.trim() === label,
  )!

describe('calendar', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    entriesApi.mockReset()
    entriesApi.mockResolvedValue([])
    Object.values(calendar.api).forEach((mock) => mock.mockReset())
    calendar.options = null
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    localStorage.clear()
  })

  async function page(options: { flags?: Record<string, boolean>; path?: string } = {}) {
    const result = await mountView(CalendarView, {
      user: makeUser({ is_it_staff: true, permissions: ALL_PERMISSIONS }),
      ...options,
    })
    unmount = () => result.wrapper.unmount()
    return result
  }

  describe('kinds', () => {
    it('offers every kind while all features are on', async () => {
      await page()
      expect(chips()).toEqual([
        ['Request', 'true'],
        ['Pickup', 'true'],
        ['Return due', 'true'],
        ['Delivery', 'true'],
        ['Warranty ends', 'true'],
        ['License ends', 'true'],
      ])
    })

    it('offers only kinds whose feature is on, and asks only for those', async () => {
      await page({ flags: { calendar_warranty: false, calendar_deliveries: false } })
      expect(chips().map(([label]) => label)).toEqual([
        'Request',
        'Pickup',
        'Return due',
        'License ends',
      ])
      await calendar.options!.events(MONTH)
      expect(entriesApi).toHaveBeenCalledWith(
        '2026-10-26',
        '2026-12-07',
        ['loan', 'pickup', 'return', 'license'],
        null,
      )
    })

    it('hides a kind, remembers it and loads again without it', async () => {
      await page()
      await click(chip('Pickup'))
      expect(chip('Pickup').getAttribute('aria-pressed')).toBe('false')
      expect(calendar.api.refetchEvents).toHaveBeenCalled()
      expect(JSON.parse(localStorage.getItem('argus.calendar-hidden-kinds')!)).toEqual(['pickup'])
      await calendar.options!.events(MONTH)
      expect(entriesApi.mock.calls[0]![2]).not.toContain('pickup')
    })

    it('asks nothing with every kind hidden', async () => {
      localStorage.setItem(
        'argus.calendar-hidden-kinds',
        JSON.stringify(['loan', 'pickup', 'return', 'delivery', 'warranty', 'license']),
      )
      await page()
      expect(await calendar.options!.events(MONTH)).toEqual([])
      expect(entriesApi).not.toHaveBeenCalled()
    })
  })

  it('asks for the requests of whom the list link names', async () => {
    await page({ path: '/calendar?assigned=me' })
    await calendar.options!.events(MONTH)
    expect(entriesApi.mock.calls[0]![3]).toBe('me')
  })

  it('switches the view and keeps it', async () => {
    await page()
    expect(calendar.options!.initialView).toBe('dayGridMonth')
    await click(
      [...document.body.querySelectorAll('.n-radio-button')].find(
        (b) => b.textContent?.trim() === 'Week',
      )!,
    )
    await flushPromises()
    expect(calendar.api.changeView).toHaveBeenCalledWith('timeGridWeek')
    expect(localStorage.getItem('argus.calendar-view')).toBe('timeGridWeek')
  })

  it('shows entries by kind, overdue in red and unconfirmed as outline', async () => {
    entriesApi.mockResolvedValue([
      entry('pickup', { status: 'confirmed' }),
      entry('return', { overdue: true, status: 'handed_out' }),
      entry('warranty', { title: '3' }),
    ])
    await page()
    const events = await calendar.options!.events(MONTH)
    expect(events.map((e) => [e.title, e.color, e.className])).toEqual([
      ['Pickup: Paul Wolf', 'var(--ar-success)', 'ar-tentative'],
      ['Return: Paul Wolf', 'var(--ar-error)', undefined],
      ['Warranty ends: 3 devices', 'var(--ar-violet)', undefined],
    ])
  })

  it('opens the page an entry links to', async () => {
    const { router } = await page()
    calendar.options!.eventClick({
      event: { extendedProps: { entry: entry('loan', { link: { name: 'request', id: ID(1) } }) } },
    })
    await flushPromises()
    expect(router.currentRoute.value.fullPath).toBe(`/requests/${ID(1)}`)
  })
})

describe('calendar entries', () => {
  const t = i18n.global.t as Parameters<typeof entryLabel>[1]

  it.each<[string, Entry, string | null]>([
    ['a request', entry('loan', { link: { name: 'request', id: ID(1) } }), `/requests/${ID(1)}`],
    [
      'an order',
      entry('delivery', { link: { name: 'order', id: ID(2) } }),
      `/procurement/orders/${ID(2)}`,
    ],
    [
      'a license',
      entry('license', { link: { name: 'license', id: ID(3) } }),
      `/inventory/licenses/${ID(3)}`,
    ],
    [
      'the devices whose warranty ends that day',
      entry('warranty', { link: { name: 'assets', warranty_until: '2026-11-30' } }),
      '/inventory/assets?warranty_until=2026-11-30',
    ],
    ['nowhere without a link', entry('pickup'), null],
  ])('lead to %s', (_what, value, path) => {
    // Resolving only; no navigation, so no page is loaded.
    const router = createRouter({ history: createMemoryHistory(), routes })
    const to = entryRoute(value)
    expect(to && router.resolve(to).fullPath).toBe(path)
  })

  it('count as unconfirmed while IT has not confirmed or prepared them', () => {
    expect(isTentative(entry('loan', { status: 'submitted' }))).toBe(true)
    expect(isTentative(entry('loan', { status: 'pending_approval' }))).toBe(true)
    expect(isTentative(entry('loan', { status: 'confirmed' }))).toBe(false)
    expect(isTentative(entry('pickup', { status: 'confirmed' }))).toBe(true)
    expect(isTentative(entry('pickup', { status: 'ready' }))).toBe(false)
  })

  it('are red when overdue, whatever their kind', () => {
    expect(entryColor(entry('loan', { overdue: true }))).toBe('var(--ar-error)')
    expect(entryColor(entry('loan'))).toBe('var(--ar-primary)')
  })

  it('name a single device whose warranty ends', () => {
    expect(entryLabel(entry('warranty', { title: '1' }), t)).toBe('Warranty ends: 1 device')
    expect(entryLabel(entry('delivery', { title: 'Nordlicht' }), t)).toBe('Delivery: Nordlicht')
    expect(entryLabel(entry('loan', { title: 'REQ-2026-00042' }), t)).toBe('REQ-2026-00042')
  })
})
