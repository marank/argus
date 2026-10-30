import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { assetModelsApi } from '@/api/masterdata'
import { needsApi, ordersApi } from '@/api/procurement'
import type { Schemas } from '@/api/types'
import NeedsView from '@/views/procurement/NeedsView.vue'
import OrderListView from '@/views/procurement/OrderListView.vue'

import { button, click } from './dom'
import {
  bodyText,
  categoryRef,
  headerHas,
  locationRef,
  modelRef,
  mountPage,
  page,
  stubPickers,
  titled,
  userRef,
} from './inventoryHelpers'

type RequestNeed = Schemas['AssetRequestNeedOut']
type ConsumableNeed = Schemas['ConsumableNeedOut']

function requestNeed(
  overrides: Partial<RequestNeed> = {},
  item: Partial<RequestNeed['asset_request_item']> = {},
): RequestNeed {
  return {
    asset_request: {
      id: 'r1',
      number: 'REQ-0007',
      title: 'Laptop for new hire',
      status: 'confirmed',
      start_date: '2026-11-15',
      requester: userRef('Max Muster', 'u2'),
    },
    asset_request_item: {
      id: 'ri1',
      label: 'Dell Latitude 5450',
      asset_model: modelRef(),
      category: null,
      default_supplier: { id: 's1', name: 'Nordlicht' },
      is_free_text: false,
      ...item,
    },
    missing: 2,
    available: 0,
    on_order: 0,
    to_order: 2,
    ...overrides,
  }
}

function consumableNeed(overrides: Partial<ConsumableNeed> = {}): ConsumableNeed {
  return {
    consumable: {
      id: 'k1',
      model: modelRef('Toner 207A', 'bulk', 'm5'),
      location: locationRef(),
      quantity: 2,
      min_quantity: 10,
      default_supplier: { id: 's2', name: 'Printer World' },
    },
    missing: 8,
    on_order: 0,
    to_order: 8,
    ...overrides,
  }
}

const created = { id: 'o9', number: 'PO-2026-0009' } as Schemas['PurchaseOrderOut']

let unmount: (() => void) | null = null
beforeEach(() => {
  stubPickers()
})
afterEach(() => {
  unmount?.()
  unmount = null
  document.body.innerHTML = ''
  vi.restoreAllMocks()
})

describe('NeedsView', () => {
  async function show(needs: Partial<Schemas['NeedsOut']> = {}) {
    vi.spyOn(needsApi, 'list').mockResolvedValue({
      requests: [requestNeed()],
      consumables: [consumableNeed()],
      ...needs,
    })
    const result = await mountPage(NeedsView, {}, { permissions: { procurement: 'write' } })
    unmount = () => result.wrapper.unmount()
    return result
  }

  const card = (title: string) =>
    [...document.body.querySelectorAll<HTMLElement>('.n-card')].find((el) =>
      el.querySelector('.n-card-header')?.textContent?.includes(title),
    )!
  const rowsIn = (title: string) => [...card(title).querySelectorAll<HTMLElement>('tbody tr')]

  async function select(title: string, index = 0) {
    rowsIn(title)[index]!.querySelector<HTMLElement>('.n-checkbox')!.click()
    await flushPromises()
  }

  it('lists demand from requests with what is missing, in the pool and on order', async () => {
    await show({
      requests: [requestNeed({ missing: 3, available: 1, on_order: 1, to_order: 1 })],
    })
    const row = rowsIn('From requests')[0]!.textContent
    expect(row).toContain('Dell Latitude 5450')
    expect(row).toContain('Nordlicht')
    expect(row).toContain('REQ-0007')
    expect(row).toContain('Max Muster')
    expect(row).toMatch(/3\s*1\s*1\s*1$/)
  })

  it('marks custom requests as such', async () => {
    await show({
      requests: [
        requestNeed({}, { asset_model: null, is_free_text: true, label: 'Ergonomic mouse' }),
      ],
    })
    expect(rowsIn('From requests')[0]!.textContent).toContain('Ergonomic mouseCustom request')
  })

  it('lists consumables below their minimum', async () => {
    await show()
    const row = rowsIn('Consumables below minimum')[0]!.textContent
    expect(row).toContain('Dell Toner 207A')
    expect(row).toContain('HQ / Main office')
    expect(row).toContain('8')
  })

  it('says when nothing is to be ordered', async () => {
    await show({ requests: [], consumables: [] })
    expect(card('From requests').textContent).toContain('No open demand.')
    expect(card('Consumables below minimum').textContent).toContain('No open demand.')
  })

  it('hides lines the pool or an order covers until asked, and never selects them', async () => {
    await show({
      requests: [
        requestNeed({ on_order: 2, to_order: 0 }, { id: 'ri2', label: 'Covered laptop' }),
        requestNeed(),
      ],
    })
    expect(rowsIn('From requests')).toHaveLength(1)
    expect(card('From requests').textContent).not.toContain('Covered laptop')

    card('From requests').querySelector<HTMLElement>('.n-card-header .n-checkbox')!.click()
    await flushPromises()
    expect(card('From requests').textContent).toContain('Show 1 covered line')
    const covered = rowsIn('From requests').find((r) => r.textContent?.includes('Covered laptop'))!
    expect(covered.querySelector('.n-checkbox')!.classList).toContain('n-checkbox--disabled')
  })

  it('says there is no demand when every line is covered', async () => {
    await show({ requests: [requestNeed({ available: 5, to_order: 0 })] })
    expect(card('From requests').textContent).toContain('No open demand.')
  })

  it('waits for a selection before creating an order', async () => {
    await show()
    expect(button('Create order (0)').disabled).toBe(true)
    await select('From requests')
    await select('Consumables below minimum')
    expect(button('Create order (2)').disabled).toBe(false)
  })

  it('combines the selected lines into one order with the first supplier', async () => {
    const create = vi.spyOn(ordersApi, 'create').mockResolvedValue(created)
    const { router } = await show()
    await select('From requests')
    await select('Consumables below minimum')
    await click('Create order (2)')
    const modal = document.body.querySelector('.n-modal')!.textContent
    expect(modal).toContain('Dell Latitude 5450 · REQ-0007')
    expect(modal).toContain('Dell Toner 207A')
    await click(button('Create order'))

    expect(create).toHaveBeenCalledWith({
      supplier: 's1',
      expected_date: null,
      supplier_reference: '',
      delivery_location: null,
      notes: '',
      lines: [
        {
          asset_model: 'm1',
          description: '',
          quantity: 2,
          unit_price: null,
          asset_request_item: 'ri1',
        },
        {
          asset_model: 'm5',
          description: '',
          quantity: 8,
          unit_price: null,
          asset_request_item: null,
        },
      ],
    })
    expect(bodyText()).toContain('Order PO-2026-0009 created')
    expect(router.currentRoute.value.fullPath).toBe('/order/o9')
  })

  it("takes the consumable's supplier when no request line is selected", async () => {
    const create = vi.spyOn(ordersApi, 'create').mockResolvedValue(created)
    await show()
    await select('Consumables below minimum')
    await click('Create order (1)')
    await click(button('Create order'))
    expect(create).toHaveBeenCalledWith(expect.objectContaining({ supplier: 's2' }))
  })

  it('orders a custom request by its description, with models of its category offered', async () => {
    const create = vi.spyOn(ordersApi, 'create').mockResolvedValue(created)
    await show({
      requests: [
        requestNeed(
          {},
          {
            asset_model: null,
            category: categoryRef('Mice'),
            is_free_text: true,
            label: 'Ergonomic mouse',
            default_supplier: null,
          },
        ),
      ],
    })
    await select('From requests')
    await click('Create order (1)')
    expect(assetModelsApi.list).toHaveBeenCalledWith(expect.objectContaining({ category: 'c1' }))
    await click(button('Create order'))
    expect(create).toHaveBeenCalledWith(
      expect.objectContaining({
        supplier: null,
        lines: [
          expect.objectContaining({ asset_model: null, description: 'Ergonomic mouse · REQ-0007' }),
        ],
      }),
    )
  })

  it('leaves out lines removed from the draft', async () => {
    const create = vi.spyOn(ordersApi, 'create').mockResolvedValue(created)
    await show()
    await select('From requests')
    await select('Consumables below minimum')
    await click('Create order (2)')
    const removes = document.body.querySelectorAll<HTMLButtonElement>(
      '.n-modal tbody td:last-child button',
    )
    await click(removes[0]!)
    await click(button('Create order'))
    expect(create.mock.calls[0]![0].lines).toEqual([
      expect.objectContaining({ asset_model: 'm5', quantity: 8 }),
    ])
  })

  it('reloads demand and drops the selection on refresh', async () => {
    await show()
    await select('From requests')
    await click('Refresh')
    expect(needsApi.list).toHaveBeenCalledTimes(2)
    expect(button('Create order (0)').disabled).toBe(true)
  })
})

describe('OrderListView', () => {
  async function show(
    url = '/',
    permissions: Record<string, 'read' | 'write'> = { procurement: 'write' },
  ) {
    const result = await mountPage(OrderListView, {}, { permissions, url })
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('shows "ordered" from the dashboard including partly received orders', async () => {
    const list = vi.spyOn(ordersApi, 'list').mockResolvedValue(page([]))
    await show('/orders?status=ordered')
    expect(list).toHaveBeenCalledWith(
      expect.objectContaining({ status: ['ordered', 'partially_received'] }),
    )
  })

  it('starts a new order as a draft with one line and opens it', async () => {
    vi.spyOn(ordersApi, 'list').mockResolvedValue(page([]))
    const create = vi.spyOn(ordersApi, 'create').mockResolvedValue(created)
    const { router } = await show()
    await click('New order')
    expect(create).toHaveBeenCalledWith(
      expect.objectContaining({
        supplier: null,
        lines: [{ asset_model: null, description: '—', quantity: 1, unit_price: null }],
      }),
    )
    expect(router.currentRoute.value.fullPath).toBe('/order/o9')
  })

  it('opens an order from its row', async () => {
    vi.spyOn(ordersApi, 'list').mockResolvedValue(
      page([
        {
          id: 'o3',
          number: 'PO-2026-0003',
          status: 'ordered',
          supplier: { id: 's1', name: 'Nordlicht' },
          supplier_reference: 'AB-77',
          line_count: 2,
          total: '1798.00',
          order_date: '2026-10-25',
          expected_date: null,
          created_at: '2026-10-20T09:00:00Z',
        },
      ]),
    )
    const { router } = await show()
    const row = document.body.querySelector<HTMLElement>('tbody tr')!
    expect(row.textContent).toContain('PO-2026-0003')
    expect(row.textContent).toContain('Nordlicht')
    expect(row.textContent).toContain('Ordered')
    row.click()
    await flushPromises()
    expect(router.currentRoute.value.fullPath).toBe('/order/o3')
  })

  it('offers no new order without the right to change procurement', async () => {
    vi.spyOn(ordersApi, 'list').mockResolvedValue(page([]))
    await show('/', { procurement: 'read' })
    expect(headerHas('New order')).toBe(false)
    expect(titled('Delete')).toEqual([])
  })
})
