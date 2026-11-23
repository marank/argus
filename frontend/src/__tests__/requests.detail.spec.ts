import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import RequestDetailView from '@/views/requests/RequestDetailView.vue'

import {
  button,
  buttons,
  chooseMenuEntry,
  click,
  control,
  menuEntries,
  rowWith,
  typeInto,
} from './dom'
import {
  JANE,
  REQUEST_ID,
  allocatedRequest,
  device,
  lentRequest,
  makeItem,
  makeRequest,
  modal,
  openModal,
  mountWithApp,
  screen,
  seat,
} from './requestsHelpers'

type AssetRequest = Schemas['AssetRequestOut']

const api = vi.hoisted(() => {
  const fn = () => vi.fn<(...args: never[]) => Promise<unknown>>()
  return {
    requests: {
      get: fn(),
      confirm: fn(),
      reject: fn(),
      schedule: fn(),
      markReady: fn(),
      handOut: fn(),
      returnDevices: fn(),
      extend: fn(),
      remind: fn(),
      reopen: fn(),
      cancel: fn(),
      candidates: fn(),
      allocate: fn(),
      autoAllocate: fn(),
      removeAllocation: fn(),
      handOutUnrecorded: fn(),
      returnUnrecorded: fn(),
      resolveItem: fn(),
      assign: fn(),
    },
    portal: { availability: fn() },
    locations: vi.fn<(...args: never[]) => Promise<unknown>>(async () => ({ items: [], count: 0 })),
  }
})

vi.mock('@/api/requests', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/requests')>()),
  requestsApi: api.requests,
  portalApi: api.portal,
}))

// The selects in the cards and dialogs load their options; an empty list will do.
vi.mock('@/api/accounts', async (importOriginal) => {
  const empty = { list: async () => ({ items: [], count: 0 }) }
  return {
    ...(await importOriginal<typeof import('@/api/accounts')>()),
    usersApi: empty,
    teamsApi: empty,
  }
})
vi.mock('@/api/masterdata', async (importOriginal) => {
  const empty = { list: async () => ({ items: [], count: 0 }) }
  return {
    ...(await importOriginal<typeof import('@/api/masterdata')>()),
    locationsApi: { list: api.locations },
    assetModelsApi: empty,
    suppliersApi: empty,
  }
})

const PICKUP_POINT = { id: 'loc-1', name: 'IT desk', full_name: 'HQ / IT desk' }

describe('RequestDetailView', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api.requests).forEach((mock) => mock.mockReset())
    api.portal.availability.mockReset()
    api.portal.availability.mockResolvedValue({ models: {}, categories: {} })
    api.requests.candidates.mockResolvedValue({
      assets: [],
      consumables: [],
      devices: [],
      licenses: [],
    })
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
  })

  async function open(request: AssetRequest, permission: 'read' | 'write' = 'write') {
    api.requests.get.mockResolvedValue(request)
    const result = await mountWithApp(RequestDetailView, { id: REQUEST_ID }, { permission })
    unmount = () => result.wrapper.unmount()
    return result
  }

  /** Opens the "More actions" menu and picks an entry. */
  async function menu(label: string) {
    await click('More actions')
    await chooseMenuEntry(label)
  }

  const moreActions = async () => {
    await click('More actions')
    return menuEntries()
  }

  describe('a submitted request', () => {
    it('offers to confirm or reject it and says so as next step', async () => {
      await open(makeRequest())
      expect(buttons('Confirm')).toHaveLength(1)
      expect(buttons('Reject')).toHaveLength(1)
      expect(buttons('Finish preparation')).toEqual([])
      expect(screen()).toContain('Check the availability of the items, then confirm or reject')
    })

    it('shows what the pool holds in the period, counted from the earlier pickup wish', async () => {
      api.portal.availability.mockResolvedValue({
        models: { 'model-Laptop 14': { available: 3, reserved: 1 } },
        categories: {},
      })
      await open(makeRequest({ requested_pickup_date: '2026-10-30' }))
      expect(api.portal.availability).toHaveBeenCalledWith({
        start: '2026-10-30',
        end: '2026-11-06',
      })
      expect(screen()).toContain('Free in the period: 3')
    })

    it('asks the pool open-ended for a permanent request', async () => {
      await open(makeRequest({ duration: 'permanent', end_date: null }))
      expect(api.portal.availability).toHaveBeenCalledWith({
        start: '2026-11-02',
        permanent: true,
      })
    })

    it('confirms with fewer devices than requested and a comment for the employee', async () => {
      const request = makeRequest({ items: [makeItem({ quantity_requested: 3 })] })
      api.requests.confirm.mockResolvedValue({ ...request, status: 'confirmed' })
      await open(request)

      await click('Confirm')
      expect(openModal().textContent).toContain('Confirm request')
      typeInto(openModal().querySelector('.qty input'), '2')
      typeInto(openModal().querySelector('textarea'), 'Only two left.')
      await flushPromises()
      await click('Confirm')

      expect(api.requests.confirm).toHaveBeenCalledWith(REQUEST_ID, {
        items: [{ id: 'item-1', quantity_confirmed: 2 }],
        comment: 'Only two left.',
      })
      expect(modal()).toBeNull()
      // Confirmed: the next step is preparing it.
      expect(buttons('Reject')).toEqual([])
      expect(screen()).toContain('Allocate specific devices')
    })

    it('rejects only with a reason for the employee', async () => {
      api.requests.reject.mockResolvedValue(makeRequest({ status: 'rejected' }))
      await open(makeRequest())
      await click('Reject')
      expect(button('Reject').disabled).toBe(true)

      typeInto(openModal().querySelector('textarea'), 'No budget this year.')
      await flushPromises()
      await click('Reject')

      expect(api.requests.reject).toHaveBeenCalledWith(REQUEST_ID, 'No budget this year.')
      expect(buttons('Confirm')).toEqual([])
    })

    it('keeps the reject dialog open when rejecting fails', async () => {
      api.requests.reject.mockRejectedValue(new ApiError(409, 'The request is already confirmed.'))
      await open(makeRequest())
      await click('Reject')
      typeInto(openModal().querySelector('textarea'), 'No budget this year.')
      await flushPromises()
      await click('Reject')

      expect(screen()).toContain('The request is already confirmed.')
      expect(modal()).not.toBeNull()
    })

    it('can be cancelled from the menu after confirming the question', async () => {
      api.requests.cancel.mockResolvedValue(makeRequest({ status: 'cancelled' }))
      await open(makeRequest())
      await menu('Cancel request')
      expect(screen()).toContain('Cancel this request? Allocated devices are returned to the pool.')
      await click('Confirm')
      expect(api.requests.cancel).toHaveBeenCalledWith(REQUEST_ID)
      expect(buttons('Confirm')).toEqual([])
    })

    it('stays as it is when cancelling is called off', async () => {
      await open(makeRequest())
      await menu('Cancel request')
      await click('Cancel')
      expect(api.requests.cancel).not.toHaveBeenCalled()
    })

    it('is replaced in the request cart, a direct hand-out in its own', async () => {
      const { router } = await open(makeRequest())
      await menu('Replace')
      expect(router.currentRoute.value.name).toBe('portal-new')
      expect(router.currentRoute.value.query).toEqual({ replace: REQUEST_ID })
      unmount?.()

      const direct = await open(makeRequest({ origin: 'direct', status: 'confirmed' }))
      await menu('Replace')
      expect(direct.router.currentRoute.value.name).toBe('direct-handout')
    })
  })

  describe('a confirmed request', () => {
    it('cannot be marked ready while devices are missing, but they can be ordered', async () => {
      await open(makeRequest({ status: 'confirmed', items: [makeItem({ quantity_confirmed: 1 })] }))
      expect(buttons('Finish preparation')).toEqual([])
      expect(buttons('Order missing')).toHaveLength(1)
      expect(screen()).toContain('Allocate specific devices')
    })

    it('marks a fully allocated request ready with the planned pickup', async () => {
      const request = allocatedRequest({
        pickup_at: '2026-11-02T08:00:00.000Z',
        pickup_location: PICKUP_POINT,
      })
      api.requests.markReady.mockResolvedValue({ ...request, status: 'ready' })
      await open(request)
      expect(screen()).toContain('Everything is allocated. Finish the preparation')

      await click('Finish preparation')
      expect(openModal().textContent).toContain('How will the devices reach the employee?')
      await click('Finish preparation')

      expect(api.requests.markReady).toHaveBeenCalledWith(REQUEST_ID, {
        handover_mode: 'pickup',
        skip_device_check: false,
        pickup_at: '2026-11-02T08:00:00.000Z',
        pickup_location: 'loc-1',
        notify: true,
      })
      expect(buttons('Hand out')).toHaveLength(1)
    })

    it('does not notify the employee by default for a direct hand-out', async () => {
      const request = allocatedRequest({ origin: 'direct' })
      api.requests.markReady.mockResolvedValue({ ...request, status: 'ready' })
      await open(request)
      await click('Finish preparation')
      await click('Finish preparation')
      expect(api.requests.markReady).toHaveBeenCalledWith(
        REQUEST_ID,
        expect.objectContaining({ notify: false }),
      )
    })

    it('drops the device check and the pickup place when IT delivers', async () => {
      const request = allocatedRequest({
        skip_device_check: true,
        pickup_at: '2026-11-02T08:00:00.000Z',
      })
      api.requests.markReady.mockResolvedValue({ ...request, status: 'ready' })
      await open(request)
      await click('Finish preparation')
      expect(openModal().textContent).toContain('Skip the device check')

      const delivery = [...openModal().querySelectorAll<HTMLElement>('[role="radio"]')].find((b) =>
        b.textContent?.includes('Delivered by IT'),
      )!
      delivery.click()
      await flushPromises()
      expect(openModal().textContent).toContain('Delivery on')
      expect(openModal().textContent).not.toContain('Pickup location')
      expect(openModal().textContent).not.toContain('Skip the device check')
      await click('Finish preparation')

      expect(api.requests.markReady).toHaveBeenCalledWith(
        REQUEST_ID,
        expect.objectContaining({ handover_mode: 'delivery', skip_device_check: false }),
      )
    })

    it('asks for date and place before telling the employee', async () => {
      await open(allocatedRequest())
      await click('Finish preparation')
      expect(openModal().textContent).toContain('Enter date and place to notify the employee.')
      const submit = [...openModal().querySelectorAll('button')].find((b) =>
        b.textContent?.includes('Finish preparation'),
      )!
      expect(submit.disabled).toBe(true)

      // Without a message, nothing has to be planned.
      control('switch', 'Notify the employee', openModal()).click()
      await flushPromises()
      expect(submit.disabled).toBe(false)
    })

    it('proposes the next full hour and the only pickup point', async () => {
      api.locations.mockResolvedValue({ items: [PICKUP_POINT], count: 1 })
      const request = allocatedRequest()
      api.requests.markReady.mockResolvedValue({ ...request, status: 'ready' })
      try {
        await open(request)
        await click('Finish preparation')
        const next = new Date()
        next.setHours(next.getHours() + 1, 0, 0, 0)
        await click('Finish preparation')
        expect(api.requests.markReady).toHaveBeenCalledWith(
          REQUEST_ID,
          expect.objectContaining({ pickup_at: next.toISOString(), pickup_location: 'loc-1' }),
        )
      } finally {
        api.locations.mockResolvedValue({ items: [], count: 0 })
      }
    })

    it('keeps the ready dialog open and shows why marking ready failed', async () => {
      api.requests.markReady.mockRejectedValue(new ApiError(409, 'INV-001 is no longer available.'))
      await open(
        allocatedRequest({ pickup_at: '2026-11-02T08:00:00.000Z', pickup_location: PICKUP_POINT }),
      )
      await click('Finish preparation')
      await click('Finish preparation')
      expect(screen()).toContain('INV-001 is no longer available.')
      expect(openModal().textContent).toContain('How will the devices reach the employee?')
      expect(buttons('Hand out')).toEqual([])
    })

    it('releases license seats right away, as there is nothing to collect', async () => {
      const request = allocatedRequest({
        items: [
          makeItem({
            is_software: true,
            quantity_confirmed: 1,
            allocations: [seat('Office 365')],
          }),
        ],
      })
      api.requests.markReady.mockResolvedValue({ ...request, status: 'handed_out' })
      await open(request)
      expect(screen()).toContain('Release the licenses to complete the hand-out')

      await click('Release licenses')
      expect(screen()).toContain('The request contains no devices to collect.')
      await click('Confirm')

      expect(api.requests.markReady).toHaveBeenCalledWith(REQUEST_ID, {
        handover_mode: 'pickup',
        skip_device_check: false,
        pickup_at: null,
        pickup_location: null,
        notify: true,
      })
    })

    it('edits the confirmed quantities, never below what is allocated', async () => {
      await open(
        allocatedRequest({
          items: [
            makeItem({
              quantity_requested: 3,
              quantity_confirmed: 2,
              allocations: [device('INV-001', 'Laptop 14')],
            }),
          ],
        }),
      )
      await click('Edit')
      expect(openModal().textContent).toContain('Edit quantities')
      expect(openModal().textContent).toContain('1 already allocated')
      expect(openModal().querySelector<HTMLInputElement>('.qty input')!.value).toBe('2')
      expect(buttons('Save', openModal())).toHaveLength(1)
    })
  })

  describe('a ready request', () => {
    const readyRequest = (overrides: Partial<AssetRequest> = {}) =>
      allocatedRequest({
        status: 'ready',
        handover_mode: 'collect',
        items: [
          makeItem({
            quantity_requested: 2,
            quantity_confirmed: 2,
            allocations: [device('INV-001', 'Laptop 14'), device('INV-002', 'Laptop 14')],
          }),
        ],
        ...overrides,
      })

    it('tells IT to hand the devices over and record it', async () => {
      await open(readyRequest())
      expect(screen()).toContain('Hand the devices to Jane Doe, then record the hand-out.')
    })

    it('warns that handing out here skips the planned signature', async () => {
      await open(readyRequest())
      await click('Hand out')
      expect(openModal().textContent).not.toContain('was planned')

      await open(readyRequest({ handover_mode: 'pickup' }))
      await click('Hand out')
      expect(openModal().textContent).toContain(
        'Pickup with a signature at the terminal was planned.',
      )
    })

    it('marks a pickup date that has passed', async () => {
      await open(readyRequest({ pickup_at: '2020-01-06T09:00:00Z' }))
      expect(document.querySelector('dd.warning')?.textContent).toContain('passed')
    })

    it('records who received the devices, with notes only for devices that have one', async () => {
      const request = readyRequest()
      api.requests.handOut.mockResolvedValue(lentRequest())
      await open(request)
      await click('Hand out')

      expect(openModal().querySelectorAll('.device input')).toHaveLength(2)
      typeInto(rowWith('INV-002', openModal(), '.device').querySelector('input'), 'Charger missing')
      await flushPromises()
      await click('Hand out')

      expect(api.requests.handOut).toHaveBeenCalledWith(REQUEST_ID, {
        method: 'direct',
        received_by: JANE.id,
        received_by_name: '',
        location: '',
        notes: '',
        allocation_notes: [{ allocation: 'alloc-INV-002', note: 'Charger missing' }],
      })
      expect(modal()).toBeNull()
      expect(buttons('Take back')).toHaveLength(1)
    })

    it('records a delivery with the place it went to', async () => {
      api.requests.handOut.mockResolvedValue(lentRequest())
      await open(readyRequest({ handover_mode: 'delivery' }))
      await click('Hand out')
      typeInto(openModal().querySelector('input[placeholder="e.g. office 2.14"]'), 'Office 2.14')
      await flushPromises()
      await click('Hand out')

      expect(api.requests.handOut).toHaveBeenCalledWith(
        REQUEST_ID,
        expect.objectContaining({ method: 'delivered', location: 'Office 2.14' }),
      )
    })

    it('keeps the hand-out dialog open when the server refuses', async () => {
      api.requests.handOut.mockRejectedValue(new ApiError(409, 'The request was cancelled.'))
      await open(readyRequest())
      await click('Hand out')
      await click('Hand out')
      expect(screen()).toContain('The request was cancelled.')
      expect(openModal().textContent).toContain('Notes per device')
    })

    it('offers changing the handover, going back to preparation and cancelling', async () => {
      await open(readyRequest())
      expect(await moreActions()).toEqual([
        'Change handover',
        'Back to preparation',
        'Replace',
        'Cancel request',
      ])
    })

    it('goes back to preparation after confirming', async () => {
      api.requests.reopen.mockResolvedValue(readyRequest({ status: 'confirmed' }))
      await open(readyRequest())
      await menu('Back to preparation')
      expect(screen()).toContain('It is removed from the pickup terminal')
      await click('Confirm')
      expect(api.requests.reopen).toHaveBeenCalledWith(REQUEST_ID)
      expect(buttons('Hand out')).toEqual([])
    })

    it('changes how the devices reach the employee', async () => {
      const request = readyRequest({
        pickup_at: '2026-11-02T08:00:00.000Z',
        pickup_location: PICKUP_POINT,
      })
      api.requests.schedule.mockResolvedValue(request)
      await open(request)
      await menu('Change handover')
      expect(openModal().textContent).toContain('Change handover')
      await click('Save')

      expect(api.requests.schedule).toHaveBeenCalledWith(REQUEST_ID, {
        pickup_at: '2026-11-02T08:00:00.000Z',
        pickup_location: 'loc-1',
        handover_mode: 'collect',
        notify: true,
      })
    })
  })

  describe('a request handed out outside the system', () => {
    const unrecorded = (overrides: Partial<AssetRequest> = {}) =>
      makeRequest({
        status: 'handed_out',
        devices_unrecorded: true,
        items: [makeItem({ quantity_confirmed: 1 })],
        ...overrides,
      })

    it('is marked handed out from a confirmed request missing devices', async () => {
      api.requests.handOutUnrecorded.mockResolvedValue(unrecorded())
      await open(makeRequest({ status: 'confirmed', items: [makeItem({ quantity_confirmed: 1 })] }))
      await click('Mark as handed out')
      expect(screen()).toContain(
        'Hand out without recorded devices? Without a device: 1× Acme Laptop 14.',
      )
      await click('Confirm')
      expect(api.requests.handOutUnrecorded).toHaveBeenCalledWith(REQUEST_ID)
      expect(screen()).toContain('Handed out without recorded devices. Record them below')
    })

    it('stays as it is when the question is called off', async () => {
      await open(makeRequest({ status: 'confirmed', items: [makeItem({ quantity_confirmed: 1 })] }))
      await click('Mark as handed out')
      await click('Cancel')
      expect(api.requests.handOutUnrecorded).not.toHaveBeenCalled()
    })

    it('records devices later, without picking them from the pool', async () => {
      await open(unrecorded())
      expect(screen()).toContain('Record devices')
      expect(screen()).toContain('counts as with the employee since the hand-out')
      // Scanned in, not filled from the pool.
      expect(document.body.querySelector('.scan-combobox')).not.toBeNull()
      expect(buttons('Automatically')).toEqual([])
    })

    it('is marked returned without devices after confirming', async () => {
      api.requests.returnUnrecorded.mockResolvedValue(
        unrecorded({ status: 'completed', devices_unrecorded: false }),
      )
      await open(unrecorded())
      await click('Mark as returned')
      expect(screen()).toContain('No devices can be recorded afterwards.')
      await click('Confirm')
      expect(api.requests.returnUnrecorded).toHaveBeenCalledWith(REQUEST_ID)
      expect(buttons('Mark as returned')).toEqual([])
    })

    it('keeps recording open for a permanent hand-out, with nothing to take back', async () => {
      await open(unrecorded({ status: 'completed', duration: 'permanent', end_date: null }))
      expect(screen()).toContain(
        'Handed out without recorded devices. Record them below once known.',
      )
      expect(buttons('Mark as returned')).toEqual([])
      expect(screen()).toContain('Record devices')
    })
  })

  describe('a temporary request on loan', () => {
    it('shows the return date and offers extending and taking back', async () => {
      await open(lentRequest())
      expect(screen()).toContain('The devices are on loan until 11/06/2026.')
      expect(buttons('Extend loan')).toHaveLength(1)
      expect(buttons('Take back')).toHaveLength(1)
      expect(await moreActions()).toEqual(['Send return reminder'])
    })

    it('takes back all devices, marking one as damaged', async () => {
      api.requests.returnDevices.mockResolvedValue(lentRequest({ status: 'completed' }))
      await open(lentRequest())
      await click('Take back')

      expect(openModal().querySelectorAll('.device')).toHaveLength(2)
      const broken = rowWith('INV-002', openModal(), '.device')
      control('checkbox', 'Damaged', broken).click()
      typeInto(broken.querySelector('input'), 'Cracked display')
      typeInto(openModal().querySelector('textarea'), 'Returned at the desk.')
      await flushPromises()
      await click('Take back')

      expect(api.requests.returnDevices).toHaveBeenCalledWith(REQUEST_ID, {
        allocations: null,
        notes: 'Returned at the desk.',
        allocation_notes: [{ allocation: 'alloc-INV-002', note: 'Cracked display' }],
        damaged: ['alloc-INV-002'],
      })
    })

    it('takes back only the selected devices', async () => {
      api.requests.returnDevices.mockResolvedValue(lentRequest())
      await open(lentRequest())
      await click('Take back')

      await click(rowWith('INV-001', openModal(), '.device').querySelector('[role="checkbox"]')!)
      expect(buttons('Take back')).toHaveLength(1) // only the page's button now
      await click('Take back selected')

      expect(api.requests.returnDevices).toHaveBeenCalledWith(
        REQUEST_ID,
        expect.objectContaining({ allocations: ['alloc-INV-002'], damaged: [] }),
      )
    })

    it('does not offer devices that are already back', async () => {
      const request = lentRequest()
      request.items[0]!.allocations[0]!.returned_at = '2026-11-05T10:00:00Z'
      await open(request)
      await click('Take back')
      expect(openModal().querySelectorAll('.device')).toHaveLength(1)
      expect(openModal().textContent).toContain('INV-002')
      expect(openModal().textContent).not.toContain('INV-001')
    })

    it('reminds an overdue employee from the alert', async () => {
      const request = lentRequest({
        is_overdue: true,
        reminded_at: '2026-11-07T09:30:00Z',
        reminded_by: { id: 'max', username: 'max', display_name: 'Max IT' },
      })
      api.requests.remind.mockResolvedValue(request)
      await open(request)
      expect(screen()).toContain('Return overdue since 11/06/2026')
      expect(screen()).toContain('The devices are still with Jane Doe.')
      expect(screen()).toContain('by Max IT')
      // The alert offers the reminder, so the menu does not.
      expect(document.body.querySelector('button[title="More actions"]')).toBeNull()

      await click('Send return reminder')
      expect(screen()).toContain('Email Jane Doe a reminder to return the devices?')
      await click('Confirm')
      expect(api.requests.remind).toHaveBeenCalledWith(REQUEST_ID)
      expect(screen()).toContain('Reminder sent to Jane Doe')
    })

    it('extends the loan by the chosen number of weeks', async () => {
      api.requests.extend.mockResolvedValue(lentRequest({ end_date: '2026-11-20' }))
      vi.useFakeTimers({ toFake: ['Date'] })
      vi.setSystemTime(new Date('2026-11-03T12:00:00'))
      try {
        await open(lentRequest())
        await click('Extend loan')
        expect(openModal().textContent).toContain('Current return date')
        await click('+ 2 weeks')
        await click('Extend loan')
        expect(api.requests.extend).toHaveBeenCalledWith(REQUEST_ID, '2026-11-20')
      } finally {
        vi.useRealTimers()
      }
    })
  })

  it('offers no actions to someone who may only read requests', async () => {
    await open(makeRequest(), 'read')
    expect(screen()).toContain('Training in Munich')
    expect(buttons('Confirm')).toEqual([])
    expect(buttons('Reject')).toEqual([])
    expect(document.body.querySelector('button[title="More actions"]')).toBeNull()
  })

  it('shows a read-only view of a loan without take back or extend', async () => {
    await open(lentRequest(), 'read')
    expect(buttons('Take back')).toEqual([])
    expect(buttons('Extend loan')).toEqual([])
  })
})
