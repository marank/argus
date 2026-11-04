import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Schemas } from '@/api/types'
import RequestListView from '@/views/requests/RequestListView.vue'

import { buttons } from './dom'
import { JANE, makeRequest, mountWithApp } from './requestsHelpers'

type Row = Schemas['AssetRequestListOut']

const api = vi.hoisted(() => ({
  list: vi.fn<(params: object) => Promise<{ items: Row[]; count: number }>>(),
}))

vi.mock('@/api/requests', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/requests')>()),
  requestsApi: { list: api.list },
}))
vi.mock('@/api/accounts', async (importOriginal) => {
  const empty = { list: async () => ({ items: [], count: 0 }) }
  return {
    ...(await importOriginal<typeof import('@/api/accounts')>()),
    usersApi: empty,
    teamsApi: empty,
    departmentsApi: empty,
  }
})

/** A list row, cut from the detail fixture so both follow the same API. */
function row(overrides: Partial<Row> = {}): Row {
  const {
    approval,
    assigned_team,
    assignee,
    created_at,
    department,
    duration,
    end_date,
    handover_mode,
    id,
    is_overdue,
    item_count,
    number,
    origin,
    pickup_at,
    requested_pickup_date,
    requester,
    start_date,
    status,
    summary,
    title,
    unit_count,
  } = makeRequest()
  return {
    approval,
    assigned_team,
    assignee,
    created_at,
    department,
    duration,
    end_date,
    handover_mode,
    id,
    is_overdue,
    item_count,
    number,
    origin,
    pickup_at,
    requested_pickup_date,
    requester,
    start_date,
    status,
    summary,
    title,
    unit_count,
    ...overrides,
  }
}

describe('RequestListView', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    api.list.mockReset()
    api.list.mockResolvedValue({ items: [row()], count: 1 })
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    localStorage.clear()
    vi.restoreAllMocks()
  })

  async function list(url = '/', permission: 'read' | 'write' = 'write') {
    const result = await mountWithApp(RequestListView, {}, { url, permission })
    unmount = () => result.wrapper.unmount()
    return result
  }

  const lastParams = () => api.list.mock.lastCall![0] as Record<string, unknown>

  async function pickScope(label: string) {
    const radio = [...document.body.querySelectorAll<HTMLElement>('.n-radio-button')].find(
      (r) => r.textContent?.trim() === label,
    )!
    radio.querySelector('input')!.click()
    await flushPromises()
  }

  it('shows the open requests by start date at first', async () => {
    await list()
    expect(lastParams()).toMatchObject({ open: true, overdue: null, ordering: 'start_date' })
  })

  it('opens on the overdue loans when linked so', async () => {
    await list('/?overdue=1')
    expect(lastParams()).toMatchObject({ open: null, overdue: true })
  })

  it('opens on all requests of a status when linked so', async () => {
    await list('/?status=ready')
    expect(lastParams()).toMatchObject({ open: null, status: ['ready'] })
  })

  it('switches between open, overdue and all requests', async () => {
    await list()
    await pickScope('Overdue')
    expect(lastParams()).toMatchObject({ open: null, overdue: true })
    await pickScope('All')
    expect(lastParams()).toMatchObject({ open: null, overdue: null })
  })

  it('remembers whose requests to show and asks for those', async () => {
    localStorage.setItem('argus.requests.assigned', 'me')
    await list()
    expect(lastParams()).toMatchObject({ assigned: 'me' })
  })

  it('shows what each request is about, for whom and when', async () => {
    api.list.mockResolvedValue({
      items: [
        row({ origin: 'direct' }),
        row({
          id: 'r2',
          number: 'R-2026-0043',
          title: 'New hire',
          duration: 'permanent',
          end_date: null,
          is_overdue: false,
          pickup_at: null,
          requester: { ...JANE, display_name: 'Tom Smith' },
          department: null,
        }),
      ],
      count: 2,
    })
    const { wrapper } = await list()
    const rows = wrapper.findAll('tbody tr').map((r) => r.text())
    expect(rows[0]).toContain('R-2026-0042')
    expect(rows[0]).toContain('Training in Munich')
    expect(rows[0]).toContain('direct')
    expect(rows[0]).toContain('Jane Doe')
    expect(rows[0]).toContain('Sales')
    expect(rows[0]).toContain('11/02/2026 → 11/06/2026')
    expect(rows[1]).toContain('Tom Smith')
    expect(rows[1]).toContain('11/02/2026 → ∞')
    expect(rows[1]).not.toContain('direct')
  })

  it('highlights the period of an overdue loan', async () => {
    api.list.mockResolvedValue({ items: [row({ is_overdue: true })], count: 1 })
    const { wrapper } = await list()
    expect(wrapper.find('tbody .overdue').text()).toBe('11/02/2026 → 11/06/2026')
  })

  it('shows the preferred pickup day, marked as such, until IT sets an appointment', async () => {
    api.list.mockResolvedValue({
      items: [
        row({ status: 'submitted', pickup_at: null, requested_pickup_date: '2099-11-05' }),
        row({
          id: 'r2',
          status: 'submitted',
          pickup_at: null,
          requested_pickup_date: '2000-01-03',
        }),
        row({
          id: 'r3',
          status: 'completed',
          pickup_at: null,
          requested_pickup_date: '2099-11-05',
        }),
      ],
      count: 3,
    })
    const { wrapper } = await list()
    const cells = wrapper.findAll('tbody tr').map((r) => r.findAll('td').at(-1)!)
    // The date stays in the first line; the second only marks it as a wish.
    expect(cells[0]!.find('.mono').text()).toMatch(/\d/)
    expect(cells[0]!.find('.wish').text()).toBe('Preferred')
    expect(cells[0]!.find('.wish').text()).not.toContain('passed')
    expect(cells[1]!.find('.wish').text()).toContain('· passed')
    // After the handout the wish no longer matters.
    expect(cells[2]!.find('.wish').exists()).toBe(false)
    expect(cells[2]!.text()).toBe('—')
  })

  it('opens a request from its row', async () => {
    const { wrapper, router } = await list()
    await wrapper.find('tbody tr').trigger('click')
    await flushPromises()
    expect(router.currentRoute.value.name).toBe('request')
    expect(router.currentRoute.value.params.id).toBe(row().id)
  })

  it('offers the direct hand-out only to those who may change requests', async () => {
    await list('/', 'write')
    expect(buttons('Hand out directly')).toHaveLength(1)
    unmount?.()
    document.body.innerHTML = ''

    await list('/', 'read')
    expect(buttons('Hand out directly')).toEqual([])
    expect(buttons('New request')).toHaveLength(1)
  })
})
