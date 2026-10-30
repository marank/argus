import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Schemas } from '@/api/types'
import NewRequestView from '@/views/portal/NewRequestView.vue'

import { makeUser } from './helpers'
import { button, click, hasButton, typeInto } from './dom'
import {
  assetRequest,
  bodyText,
  catalogCategory,
  catalogModel,
  field,
  mountPage,
  unmountPages,
} from './portalHelpers'

const api = vi.hoisted(() => ({
  catalog: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  createDirect: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  create: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  getAsset: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  listAssets: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  listConsumables: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  lookup: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
}))

vi.mock('@/api/requests', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/api/requests')>()
  return {
    ...original,
    portalApi: {
      ...original.portalApi,
      catalog: api.catalog,
      availability: async () => ({ categories: {}, models: {} }),
      myConsumables: async () => [],
    },
    requestsApi: { ...original.requestsApi, create: api.create, createDirect: api.createDirect },
  }
})
vi.mock('@/api/inventory', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/api/inventory')>()
  return {
    ...original,
    assetsApi: { ...original.assetsApi, get: api.getAsset, list: api.listAssets },
    consumablesApi: { ...original.consumablesApi, list: api.listConsumables },
    lookupApi: { lookup: api.lookup },
  }
})
// The cart's "request for employee" field loads people when it appears.
vi.mock('@/api/accounts', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/api/accounts')>()
  return {
    ...original,
    usersApi: { ...original.usersApi, list: async () => ({ items: [], count: 0 }) },
  }
})

const IT_STAFF = makeUser({ is_it_staff: true, permissions: { requests: 'write' } })

const T14 = catalogModel({ id: 'm-t14', full_name: 'ThinkPad T14' })
const CATALOG = [
  catalogCategory({ id: 'c-laptops', name: 'Laptops', models: [T14] }),
  catalogCategory({ id: 'c-software', name: 'Software', kind: 'software', models: [] }),
]

const modelRef = (id: string, name: string, tracking: Schemas['Tracking'] = 'serialized') => ({
  id,
  name,
  full_name: name,
  designation: '',
  tracking,
})
const LOCATION = { id: 'l1', name: 'IT store', full_name: 'HQ / IT store' }

function device(overrides: Partial<Schemas['AssetOut']> = {}): Schemas['AssetOut'] {
  return {
    id: 'a1',
    reserved_for: null,
    inventory_number: 'NB-0001',
    serial_number: 'SN-111',
    status: 'in_stock',
    model: modelRef('m-t14', 'ThinkPad T14'),
    category: {
      id: 'c-laptops',
      name: 'Laptops',
      code: 'NB',
      icon: 'laptop',
      item_name: '',
      kind: 'hardware',
    },
    manufacturer: { id: 'mf1', name: 'Lenovo' },
    location: LOCATION,
    assigned_to: null,
    assigned_since: null,
    condition: 'new',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
    hostname: '',
    imei: '',
    mac_address: '',
    is_loanable: true,
    notes: '',
    parent: null,
    purchase_date: null,
    purchase_price: null,
    supplier: null,
    warranty_until: null,
    ...overrides,
  }
}

function stock(overrides: Partial<Schemas['ConsumableOut']> = {}): Schemas['ConsumableOut'] {
  return {
    id: 's1',
    model: modelRef('m-mouse', 'Logitech Mouse', 'bulk'),
    category: device().category,
    location: LOCATION,
    quantity: 5,
    available_quantity: 2,
    reserved_quantity: 0,
    min_quantity: 0,
    is_below_minimum: false,
    ...overrides,
  }
}

const lookupResult = (assets: Schemas['AssetOut'][]) =>
  ({ kind: assets.length ? 'asset' : 'none', assets, models: [] }) satisfies Schemas['LookupOut']

async function open(url = '/portal/new?mode=direct') {
  return mountPage(NewRequestView, { url, user: IT_STAFF })
}

const SCAN = 'Scan or search inventory or serial number'
async function scan(code: string) {
  const input = field(SCAN)
  await typeInto(input, code)
  input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
  await flushPromises()
}

/** Cart lines as "inventory number model" (or only the model for catalog lines). */
const cartLines = () =>
  [...document.body.querySelectorAll('.cart .lines li')].map((l) =>
    [l.querySelector('.code')?.textContent, l.querySelector('strong')?.textContent]
      .filter(Boolean)
      .join(' '),
  )

describe('NewRequestView: direct hand-out', () => {
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
    api.catalog.mockResolvedValue(CATALOG)
    api.listAssets.mockResolvedValue({ items: [device()], count: 1 })
    api.listConsumables.mockResolvedValue({
      // An empty stock cannot be handed out and is not listed.
      items: [
        stock(),
        stock({ id: 's2', model: modelRef('m-pad', 'Mouse pad'), available_quantity: 0 }),
      ],
      count: 2,
    })
    api.createDirect.mockResolvedValue(assetRequest({ id: 'r-direct', number: 'R-2026-0200' }))
  })
  afterEach(unmountPages)

  it('lets IT choose between a request and a direct hand-out', async () => {
    const { router } = await open('/portal/new')
    expect(bodyText()).toContain('What would you like to record?')
    await click(document.body.querySelector('button.choice.direct')!)
    expect(router.currentRoute.value.query).toEqual({ mode: 'direct' })
  })

  it('employees cannot hand out directly and go straight to the request', async () => {
    await mountPage(NewRequestView, { url: '/portal/new?mode=direct', user: makeUser() })
    expect(bodyText()).toContain('Pick a category and add what you need.')
    expect(bodyText()).not.toContain('Direct hand-out')
    expect(hasButton('Change type')).toBe(false)
  })

  it('browses what a group has in stock, without software and free text', async () => {
    await open()
    expect(bodyText()).toContain('Direct hand-out')
    const groups = [...document.body.querySelectorAll('.groups .name')].map((g) => g.textContent)
    expect(groups).toEqual(['Laptops'])
    expect(api.listAssets).toHaveBeenCalledWith(
      expect.objectContaining({ category: 'c-laptops', status: ['in_stock'] }),
    )
    const rows = document.body.querySelector('.picker .rows')!.textContent
    expect(rows).toContain('NB-0001')
    expect(rows).toContain('SN-111 · IT store')
    expect(rows).toContain('Logitech Mouse')
    expect(rows).not.toContain('Mouse pad')
  })

  it('adds a scanned device in stock to the hand-out', async () => {
    api.lookup.mockResolvedValue(lookupResult([device()]))
    await open()
    await scan('NB-0001')
    expect(api.lookup).toHaveBeenCalledWith('NB-0001')
    expect(cartLines()).toEqual(['NB-0001 ThinkPad T14'])
    expect(document.body.querySelector('.picker .rows')!.textContent).toContain('selected')
    expect(field(SCAN).value).toBe('')
  })

  it('refuses a scanned device that is not in stock', async () => {
    api.lookup.mockResolvedValue(lookupResult([device({ status: 'in_use' })]))
    await open()
    await scan('NB-0001')
    expect(bodyText()).toContain('NB-0001 is not in stock (In use).')
    expect(cartLines()).toEqual([])
  })

  it('says when nothing was found for a scanned code', async () => {
    api.lookup.mockResolvedValue(lookupResult([]))
    await open()
    await scan('XX-9999')
    expect(bodyText()).toContain('No device in stock found for “XX-9999”.')
  })

  it('takes no more from a stock than it has free', async () => {
    await open()
    const add = () =>
      [...document.body.querySelectorAll('.picker .rows li')]
        .find((row) => row.textContent?.includes('Logitech Mouse'))!
        .querySelector('button')!
    await click(add())
    await click(add())
    expect(add().disabled).toBe(true)
  })

  it('records the devices and stock quantities as a direct hand-out', async () => {
    api.lookup.mockResolvedValue(lookupResult([device()]))
    const { router } = await open()
    await scan('NB-0001')
    const addMouse = [...document.body.querySelectorAll('.picker .rows li')]
      .find((row) => row.textContent?.includes('Logitech Mouse'))!
      .querySelector('button')!
    await click(addMouse)
    await click(addMouse)
    await typeInto(field('e.g. training, new hire, stocktaking'), 'New hire')
    await click(button('Submit request'))

    expect(api.create).not.toHaveBeenCalled()
    expect(api.createDirect).toHaveBeenCalledWith(
      expect.objectContaining({
        title: 'New hire',
        requester: null,
        assets: ['a1'],
        consumables: [{ consumable: 's1', quantity: 2 }],
      }),
    )
    expect(api.createDirect.mock.calls[0]![0]).not.toHaveProperty('items')
    expect(router.currentRoute.value.name).toBe('request')
    expect(router.currentRoute.value.params.id).toBe('r-direct')
  })

  it('hands out the device it was opened from', async () => {
    api.getAsset.mockResolvedValue(device())
    await open('/portal/new?mode=direct&asset=a1')
    expect(api.getAsset).toHaveBeenCalledWith('a1')
    expect(cartLines()).toEqual(['NB-0001 ThinkPad T14'])
  })

  it('requests the model of the device it was opened from', async () => {
    api.getAsset.mockResolvedValue(device())
    await open('/portal/new?mode=request&asset=a1')
    expect(cartLines()).toEqual(['ThinkPad T14'])
  })
})
