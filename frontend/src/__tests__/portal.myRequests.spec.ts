import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import MyRequestDetailView from '@/views/portal/MyRequestDetailView.vue'
import MyRequestsView from '@/views/portal/MyRequestsView.vue'

import { button, click, hasButton } from './dom'
import {
  assetRequest,
  bodyText,
  mountPage,
  requestItem,
  requestListItem,
  unmountPages,
} from './portalHelpers'

const api = vi.hoisted(() => ({
  list: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  get: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  cancel: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
}))

vi.mock('@/api/requests', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/api/requests')>()
  return {
    ...original,
    requestsApi: { ...original.requestsApi, list: api.list, get: api.get, cancel: api.cancel },
  }
})

const page = (items: Schemas['AssetRequestListOut'][]) => ({ items, count: items.length })

describe('MyRequestsView', () => {
  beforeEach(() => Object.values(api).forEach((mock) => mock.mockReset()))
  afterEach(unmountPages)

  /** One request per state an employee meets, newest first as the API delivers them. */
  function scenario() {
    return [
      requestListItem({ id: 'r-sub', number: 'R-5', title: 'Headset', status: 'submitted' }),
      requestListItem({
        id: 'r-ready',
        number: 'R-4',
        title: 'Workshop',
        status: 'ready',
        pickup_at: null,
      }),
      requestListItem({
        id: 'r-pend',
        number: 'R-3',
        title: 'Monitor',
        status: 'pending_approval',
      }),
      requestListItem({
        id: 'r-late',
        number: 'R-2',
        title: 'Trade fair',
        status: 'handed_out',
        is_overdue: true,
        end_date: '2026-09-30',
      }),
      requestListItem({ id: 'r-done', number: 'R-1', title: 'Old laptop', status: 'completed' }),
    ]
  }

  const titles = (selector: string) =>
    [...document.body.querySelectorAll(`${selector} .title`)].map((t) => t.textContent?.trim())
  const todoLine = (title: string) =>
    [...document.body.querySelectorAll('.todo')].find(
      (l) => l.querySelector('.title')?.textContent === title,
    )!

  it('loads only the employee’s own requests', async () => {
    api.list.mockResolvedValue(page([]))
    await mountPage(MyRequestsView)
    expect(api.list).toHaveBeenCalledWith(expect.objectContaining({ mine: true }))
    expect(bodyText()).toContain('No requests yet.')
  })

  it('puts first what the employee has to do: overdue returns, then pickups', async () => {
    api.list.mockResolvedValue(page(scenario()))
    await mountPage(MyRequestsView)
    expect(titles('.todo')).toEqual(['Trade fair', 'Workshop'])
    expect(todoLine('Trade fair').querySelector('.action')!.textContent).toBe('Bring back')
    expect(todoLine('Trade fair').querySelector('.todo-text')!.textContent).toBe(
      'Return overdue since 09/30/2026.',
    )
    expect(todoLine('Workshop').querySelector('.action')!.textContent).toBe('Pick up')
    expect(todoLine('Workshop').querySelector('.todo-text')!.textContent).toBe(
      'Waiting for you at IT.',
    )
  })

  it('lists the rest in progress below, what comes next first, with its status', async () => {
    api.list.mockResolvedValue(page(scenario()))
    await mountPage(MyRequestsView)
    const lines = [...document.body.querySelectorAll('.line:not(.todo):not(.closed-line)')]
    expect(lines.map((l) => l.querySelector('.title')?.textContent)).toEqual(['Headset', 'Monitor'])
    expect(lines[0]!.textContent).toContain('Submitted')
    expect(lines[1]!.textContent).toContain('Awaiting approval')
  })

  it('folds the closed requests away until asked for', async () => {
    api.list.mockResolvedValue(page(scenario()))
    await mountPage(MyRequestsView)
    expect(document.body.querySelector('.closed-line')).toBeNull()
    await click(document.body.querySelector<HTMLElement>('.toggle')!)
    const closed = document.body.querySelector('.closed-line')!.textContent
    expect(closed).toContain('Old laptop')
    expect(closed).toContain('Completed')
  })

  it('says when nothing is running', async () => {
    api.list.mockResolvedValue(page([requestListItem({ status: 'cancelled' })]))
    await mountPage(MyRequestsView)
    expect(bodyText()).toContain('No request is in progress right now.')
    expect(document.body.querySelector('.todo')).toBeNull()
  })

  it('links each request to its page', async () => {
    api.list.mockResolvedValue(page(scenario()))
    await mountPage(MyRequestsView)
    const link = document.body.querySelector<HTMLAnchorElement>('.line')!
    expect(link.getAttribute('href')).toBe('/portal/requests/r-late')
  })
})

describe('MyRequestDetailView', () => {
  beforeEach(() => Object.values(api).forEach((mock) => mock.mockReset()))
  afterEach(unmountPages)

  async function open(request: Schemas['AssetRequestOut'], url = '/portal/requests/r1') {
    api.get.mockResolvedValue(request)
    return mountPage(MyRequestDetailView, { props: { id: request.id }, url })
  }

  it.each(['pending_approval', 'submitted', 'confirmed', 'ready'] as const)(
    'can be cancelled while %s',
    async (status) => {
      await open(assetRequest({ status }))
      expect(hasButton('Cancel request')).toBe(true)
    },
  )

  it.each(['handed_out', 'completed', 'rejected', 'cancelled'] as const)(
    'can no longer be cancelled once %s',
    async (status) => {
      await open(assetRequest({ status }))
      expect(hasButton('Cancel request')).toBe(false)
    },
  )

  it('cancels after confirming and shows the new status', async () => {
    api.cancel.mockResolvedValue(assetRequest({ status: 'cancelled' }))
    await open(assetRequest({ status: 'submitted' }))
    expect(bodyText()).not.toContain('Cancelled')
    await click(button('Cancel request'))
    expect(bodyText()).toContain('Cancel this request? Allocated devices are returned to the pool.')
    await click(button('Confirm'))
    expect(api.cancel).toHaveBeenCalledWith('r1')
    expect(bodyText()).toContain('Cancelled')
    expect(hasButton('Cancel request')).toBe(false)
  })

  it('keeps the request when cancelling is dismissed', async () => {
    await open(assetRequest({ status: 'submitted' }))
    await click(button('Cancel request'))
    await click(button('Cancel'))
    expect(api.cancel).not.toHaveBeenCalled()
    expect(hasButton('Cancel request')).toBe(true)
  })

  it('shows why cancelling failed', async () => {
    api.cancel.mockRejectedValue(new ApiError(409, 'Already handed out.'))
    await open(assetRequest({ status: 'ready' }))
    await click(button('Cancel request'))
    await click(button('Confirm'))
    expect(bodyText()).toContain('Already handed out.')
    expect(hasButton('Cancel request')).toBe(true)
  })

  it.each(['rejected', 'cancelled', 'completed'] as const)(
    'offers to request a %s request again',
    async (status) => {
      await open(assetRequest({ status }))
      const again = [...document.body.querySelectorAll('a')].find((a) =>
        a.textContent?.includes('Request again'),
      )
      expect(again?.getAttribute('href')).toBe('/portal/new?from=r1')
    },
  )

  it('points to the new request instead of asking again when IT replaced it', async () => {
    await open(
      assetRequest({
        status: 'cancelled',
        events: [
          {
            id: 'e1',
            kind: 'replaced',
            at: '2026-11-20T10:00:00Z',
            actor: null,
            data: { by: 'R-2026-0043' },
          },
        ],
      }),
    )
    expect(bodyText()).toContain('IT replaced this request with R-2026-0043.')
    expect(bodyText()).not.toContain('Request again')
  })

  it('confirms a request just submitted, mentioning the approval it waits for', async () => {
    await open(assetRequest({ status: 'pending_approval' }), '/portal/requests/r1?created=1')
    expect(bodyText()).toContain(
      'Request R-2026-0042 submitted and awaiting approval by your department.',
    )
  })

  it('drops the "submitted" note once the new request is cancelled', async () => {
    api.cancel.mockResolvedValue(assetRequest({ status: 'cancelled' }))
    await open(assetRequest({ status: 'submitted' }), '/portal/requests/r1?created=1')
    expect(bodyText()).toContain('Request R-2026-0042 submitted')
    await click(button('Cancel request'))
    await click(button('Confirm'))
    expect(bodyText()).not.toContain('Request R-2026-0042 submitted')
  })

  it('shows requested and confirmed quantities and the devices set aside', async () => {
    const allocation = (id: string, number: string): Schemas['AllocationOut'] => ({
      id,
      asset: {
        id: `a-${id}`,
        inventory_number: number,
        name: '',
        serial_number: '',
        status: 'reserved',
        model: requestItem().asset_model!,
      },
      consumable: null,
      license: null,
      quantity: 1,
      category_icon: 'laptop',
      allocated_at: '2026-10-02T09:00:00Z',
      allocated_by: null,
      device_return: null,
      handed_out_at: null,
      handout_note: '',
      return_note: '',
      returned_at: null,
      returned_damaged: false,
    })
    await open(
      assetRequest({
        status: 'confirmed',
        items: [
          requestItem({
            quantity_requested: 3,
            quantity_confirmed: 2,
            note: 'One with a German keyboard',
            allocations: [allocation('al1', 'NB-0001'), allocation('al2', 'NB-0002')],
          }),
        ],
      }),
    )
    const row = document.body.querySelector('tbody tr')!
    const cells = [...row.querySelectorAll('td')].map((c) => c.textContent?.trim())
    expect(cells).toEqual(['ThinkPad T14One with a German keyboard', '3', '2', 'NB-0001, NB-0002'])
    // Fewer than asked for stands out.
    expect(row.querySelector('.reduced')?.textContent).toBe('2')
  })

  it('shows the pickup appointment once IT planned it', async () => {
    await open(
      assetRequest({
        status: 'ready',
        pickup_at: '2026-10-20T09:00:00Z',
        pickup_location: { id: 'l1', name: 'IT desk', full_name: 'HQ / IT desk' },
      }),
    )
    expect(bodyText()).toContain('HQ / IT desk')
  })
})
