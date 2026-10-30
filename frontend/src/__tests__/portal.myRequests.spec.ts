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

  const rowLabels = () =>
    [...document.body.querySelectorAll('.row-label')].map((l) =>
      l.childNodes[0]?.textContent?.trim(),
    )
  const cardTitles = () =>
    [...document.body.querySelectorAll('.cards .card strong')].map((c) => c.textContent)

  it('loads only the employee’s own requests', async () => {
    api.list.mockResolvedValue(page([]))
    await mountPage(MyRequestsView)
    expect(api.list).toHaveBeenCalledWith(expect.objectContaining({ mine: true }))
    expect(bodyText()).toContain('No requests yet.')
  })

  it('groups running requests by status with what is ready for pickup first', async () => {
    api.list.mockResolvedValue(page(scenario()))
    await mountPage(MyRequestsView)
    expect(rowLabels()).toEqual([
      'Ready for pickup',
      'Handed out',
      'Submitted',
      'Awaiting approval',
    ])
    expect(cardTitles()).toEqual(['Workshop', 'Trade fair', 'Headset', 'Monitor'])
  })

  it('says for each running request what happens next', async () => {
    api.list.mockResolvedValue(page(scenario()))
    await mountPage(MyRequestsView)
    const next = (title: string) =>
      [...document.body.querySelectorAll('.card')]
        .find((c) => c.querySelector('strong')?.textContent === title)!
        .querySelector('.next')!.textContent
    expect(next('Workshop')).toBe('Ready for pickup')
    expect(next('Headset')).toBe('Waiting for IT to confirm.')
    expect(next('Monitor')).toBe('Waiting for your department to approve.')
    expect(next('Trade fair')).toBe('Return overdue since 09/30/2026.')
  })

  it('lists closed requests apart from the running ones', async () => {
    api.list.mockResolvedValue(page(scenario()))
    await mountPage(MyRequestsView)
    const closed = document.body.querySelector('.closed')!.textContent
    expect(closed).toContain('Old laptop')
    expect(closed).toContain('Completed')
    expect(cardTitles()).not.toContain('Old laptop')
  })

  it('sorts running requests by date when asked and remembers the choice', async () => {
    api.list.mockResolvedValue(page(scenario()))
    await mountPage(MyRequestsView)
    await click(document.body.querySelector<HTMLInputElement>('input[value="date"]')!)
    expect(rowLabels()).toEqual([])
    expect(cardTitles()).toEqual(['Headset', 'Workshop', 'Monitor', 'Trade fair'])
    expect(localStorage.getItem('argus.my-requests-sort')).toBe('date')
  })

  it('says when nothing is running', async () => {
    api.list.mockResolvedValue(page([requestListItem({ status: 'cancelled' })]))
    await mountPage(MyRequestsView)
    expect(bodyText()).toContain('No request is in progress right now.')
  })

  it('links each request to its page', async () => {
    api.list.mockResolvedValue(page(scenario()))
    await mountPage(MyRequestsView)
    const link = document.body.querySelector<HTMLAnchorElement>('.cards .card')!
    expect(link.getAttribute('href')).toBe('/portal/requests/r-ready')
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
