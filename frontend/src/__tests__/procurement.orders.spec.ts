import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import { ordersApi } from '@/api/procurement'
import type { Schemas } from '@/api/types'
import OrderDetailView from '@/views/procurement/OrderDetailView.vue'

import { button, click, hasButton } from './dom'
import {
  bodyText,
  headerHas,
  locationRef,
  modelRef,
  mountPage,
  stubPickers,
  titled,
  type,
} from './inventoryHelpers'

type Line = Schemas['PurchaseOrderLineOut']
type Order = Schemas['PurchaseOrderOut']

const LAPTOP = modelRef('Latitude 5450', 'serialized', 'm1')
const TONER = modelRef('Toner 207A', 'bulk', 'm5')

function line(overrides: Partial<Line> = {}): Line {
  const quantity = overrides.quantity ?? 2
  const received = overrides.quantity_received ?? 0
  return {
    id: 'ln1',
    asset_model: LAPTOP,
    asset_request_item: null,
    description: '',
    label: 'Dell Latitude 5450',
    quantity,
    quantity_received: received,
    quantity_open: quantity - received,
    unit_price: '899.00',
    total: '1798.00',
    ...overrides,
  }
}

function order(overrides: Partial<Order> = {}): Order {
  const lines = overrides.lines ?? [line()]
  return {
    id: 'o1',
    number: 'PO-2026-0003',
    status: 'draft',
    supplier: { id: 's1', name: 'Nordlicht' },
    supplier_reference: '',
    delivery_location: locationRef(),
    expected_date: null,
    order_date: null,
    notes: '',
    created_at: '2026-10-20T09:00:00Z',
    created_by: null,
    total: '1798.00',
    line_count: lines.length,
    ...overrides,
    lines,
  }
}

describe('OrderDetailView', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-10-30T10:00:00'))
    stubPickers()
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  async function show(
    value: Order = order(),
    permissions: Record<string, 'read' | 'write'> = { procurement: 'write' },
  ) {
    vi.spyOn(ordersApi, 'get').mockResolvedValue(value)
    const result = await mountPage(OrderDetailView, { id: value.id }, { permissions })
    unmount = () => result.wrapper.unmount()
    return result
  }

  describe('a draft', () => {
    it('can be saved, marked as ordered, cancelled or deleted, not received', async () => {
      await show()
      expect(bodyText()).toContain('PO-2026-0003')
      expect(bodyText()).toContain('To order')
      expect(hasButton('Save')).toBe(true)
      expect(hasButton('Mark as ordered')).toBe(true)
      expect(hasButton('Cancel order')).toBe(true)
      expect(titled('Delete')).toHaveLength(1)
      expect(hasButton('Goods receipt')).toBe(false)
    })

    it('totals the lines as they are edited', async () => {
      await show()
      const total = () => document.body.querySelector('.n-card-header__extra')!.textContent
      expect(total()).toMatch(/1,798\.00/)
      const quantity = document.body.querySelector<HTMLInputElement>('tbody td.num input')!
      await type(quantity, '3')
      expect(total()).toMatch(/2,697\.00/)
    })

    it('saves the header and the lines with prices in cents', async () => {
      const update = vi.spyOn(ordersApi, 'update').mockResolvedValue(order())
      await show()
      await type('Supplier reference', 'AB-77')
      await click('Add line')
      const descriptions = document.body.querySelectorAll<HTMLInputElement>(
        'input[placeholder="Description"]',
      )
      await type(descriptions[1]!, 'USB-C cable')
      await click('Save')

      expect(update).toHaveBeenCalledWith('o1', {
        supplier: 's1',
        expected_date: null,
        supplier_reference: 'AB-77',
        delivery_location: 'l1',
        notes: '',
        lines: [
          {
            id: 'ln1',
            asset_model: 'm1',
            description: '',
            quantity: 2,
            unit_price: '899.00',
            asset_request_item: null,
          },
          {
            asset_model: null,
            description: 'USB-C cable',
            quantity: 1,
            unit_price: null,
          },
        ],
      })
    })

    it('keeps at least one line', async () => {
      await show()
      const removeLine = document.body.querySelector<HTMLButtonElement>(
        'tbody td:last-child button',
      )!
      expect(removeLine.disabled).toBe(true)
      await click('Add line')
      expect(removeLine.disabled).toBe(false)
    })

    it('is saved, then marked as ordered with the order details', async () => {
      const update = vi.spyOn(ordersApi, 'update').mockResolvedValue(order())
      const markOrdered = vi
        .spyOn(ordersApi, 'markOrdered')
        .mockResolvedValue(order({ status: 'ordered', order_date: '2026-10-30' }))
      await show(order({ supplier_reference: 'AB-77' }))
      await click('Mark as ordered')
      // The dialog starts from the reference given on the page.
      await type(
        [...document.body.querySelectorAll<HTMLInputElement>('.n-modal input')].at(-1)!,
        'AB-78',
      )
      await click(button('Mark as ordered'))

      expect(update).toHaveBeenCalledOnce()
      expect(markOrdered).toHaveBeenCalledWith('o1', {
        order_date: '2026-10-30',
        expected_date: null,
        supplier_reference: 'AB-78',
      })
      expect(update.mock.invocationCallOrder[0]!).toBeLessThan(
        markOrdered.mock.invocationCallOrder[0]!,
      )
      expect(bodyText()).toContain('Ordered')
      expect(headerHas('Goods receipt')).toBe(true)
      expect(headerHas('Mark as ordered')).toBe(false)
    })

    it('is not marked as ordered when saving the edits failed', async () => {
      vi.spyOn(ordersApi, 'update').mockRejectedValue(new ApiError(400, 'Quantity is missing.'))
      const markOrdered = vi.spyOn(ordersApi, 'markOrdered').mockResolvedValue(order())
      await show()
      await click('Mark as ordered')
      await click(button('Mark as ordered'))
      expect(markOrdered).not.toHaveBeenCalled()
    })

    it('is deleted after confirming', async () => {
      const remove = vi.spyOn(ordersApi, 'remove').mockResolvedValue(true)
      const { router } = await show()
      await click(titled('Delete')[0]!)
      await click('Confirm')
      expect(remove).toHaveBeenCalledWith('o1')
      expect(router.currentRoute.value.name).toBe('orders')
    })
  })

  describe('an ordered order', () => {
    const ORDERED = order({
      status: 'ordered',
      order_date: '2026-10-25',
      lines: [
        line(),
        line({
          id: 'ln2',
          asset_model: TONER,
          label: 'Dell Toner 207A',
          quantity: 10,
          unit_price: '49.00',
        }),
        line({ id: 'ln3', asset_model: null, label: 'Installation', quantity: 1 }),
        line({ id: 'ln4', label: 'Dock', quantity: 1, quantity_received: 1 }),
      ],
    })

    const receipt = (label: string) =>
      [...document.body.querySelectorAll<HTMLElement>('.receipt')].find((el) =>
        el.querySelector('.head strong')?.textContent?.includes(label),
      )

    it('shows the lines with what was received instead of editing them', async () => {
      await show(ORDERED)
      expect(document.body.querySelector('input[placeholder="Description"]')).toBeNull()
      expect(bodyText()).toContain('Received')
      expect(hasButton('Mark as ordered')).toBe(false)
      expect(hasButton('Cancel order')).toBe(true)
      expect(titled('Delete')).toEqual([])
    })

    it('receives open lines of known models only', async () => {
      await show(ORDERED)
      await click('Goods receipt')
      expect(bodyText()).toContain('Goods receipt · PO-2026-0003')
      expect(receipt('Latitude')).toBeTruthy()
      expect(receipt('Toner')).toBeTruthy()
      expect(receipt('Installation')).toBeUndefined()
      expect(receipt('Dock')).toBeUndefined()
    })

    it('takes serial numbers for devices and quantities for consumables', async () => {
      await show(ORDERED)
      await click('Goods receipt')
      expect(receipt('Latitude')!.querySelector('textarea')).toBeTruthy()
      expect(receipt('Toner')!.querySelector('textarea')).toBeNull()
      expect(receipt('Toner')!.querySelector<HTMLInputElement>('input')!.value).toBe('10')
    })

    it('receives a partial delivery with scanned serial numbers', async () => {
      const receive = vi.spyOn(ordersApi, 'receive').mockResolvedValue(
        order({
          ...ORDERED,
          status: 'partially_received',
          lines: [line({ quantity_received: 1 }), ORDERED.lines[1]!],
        }),
      )
      await show(ORDERED)
      await click('Goods receipt')
      await type(receipt('Latitude')!.querySelector<HTMLInputElement>('textarea')!, 'CN-1\n')
      expect(receipt('Latitude')!.textContent).toContain('1 serial numbers')
      // With serial numbers scanned, their count is the quantity.
      expect(receipt('Latitude')!.querySelector('input')).toBeNull()
      await type(receipt('Toner')!.querySelector<HTMLInputElement>('input')!, '0')
      await click(button('Goods receipt'))

      expect(receive).toHaveBeenCalledWith('o1', [
        { line: 'ln1', quantity: 1, serial_numbers: ['CN-1'], location: 'l1' },
      ])
      expect(bodyText()).toContain('Partially received')
      expect(headerHas('Goods receipt')).toBe(true)
      // Partly received orders can no longer be cancelled.
      expect(headerHas('Cancel order')).toBe(false)
    })

    it('receives devices by quantity when no serial numbers were scanned', async () => {
      const receive = vi
        .spyOn(ordersApi, 'receive')
        .mockResolvedValue(order({ ...ORDERED, status: 'received' }))
      await show(ORDERED)
      await click('Goods receipt')
      await click(button('Goods receipt'))
      expect(receive).toHaveBeenCalledWith('o1', [
        { line: 'ln1', quantity: 2, serial_numbers: [], location: 'l1' },
        { line: 'ln2', quantity: 10, serial_numbers: [], location: 'l1' },
      ])
      expect(bodyText()).toContain('Received')
      expect(headerHas('Save')).toBe(false)
      expect(headerHas('Goods receipt')).toBe(false)
    })

    it('keeps the receipt open when the server rejects it', async () => {
      vi.spyOn(ordersApi, 'receive').mockRejectedValue(
        new ApiError(400, 'Serial number CN-1 exists already.'),
      )
      await show(ORDERED)
      await click('Goods receipt')
      await type(receipt('Latitude')!.querySelector<HTMLInputElement>('textarea')!, 'CN-1')
      await click(button('Goods receipt'))
      expect(bodyText()).toContain('Serial number CN-1 exists already.')
      expect(receipt('Latitude')!.querySelector('textarea')!.value).toBe('CN-1')
    })

    it('is cancelled after confirming', async () => {
      const cancel = vi
        .spyOn(ordersApi, 'cancel')
        .mockResolvedValue(order({ ...ORDERED, status: 'cancelled' }))
      await show(ORDERED)
      await click('Cancel order')
      expect(bodyText()).toContain('Cancel this order?')
      await click('Confirm')
      expect(cancel).toHaveBeenCalledWith('o1')
      expect(bodyText()).toContain('Cancelled')
      expect(hasButton('Save')).toBe(false)
    })
  })

  it('is for viewing only without the right to change procurement', async () => {
    await show(order(), { procurement: 'read' })
    for (const action of ['Save', 'Mark as ordered', 'Cancel order', 'Goods receipt'])
      expect(hasButton(action)).toBe(false)
  })

  it('links lines to the request they were ordered for', async () => {
    await show(
      order({
        status: 'ordered',
        lines: [
          line({
            asset_request_item: {
              id: 'ri1',
              label: 'Laptop',
              asset_request: { id: 'r1', number: 'REQ-0007' },
            } as Schemas['LineAssetRequestItemOut'],
          }),
        ],
      }),
    )
    const link = [...document.body.querySelectorAll('a')].find((a) =>
      a.textContent?.includes('for REQ-0007'),
    )
    expect(link?.getAttribute('href')).toBe('/request/r1')
  })

  it('shows the dates and the creator', async () => {
    await show(order({ status: 'ordered', order_date: '2026-10-25' }))
    await flushPromises()
    expect(bodyText()).toMatch(/Ordered on: 10\/25\/2026/)
  })
})
