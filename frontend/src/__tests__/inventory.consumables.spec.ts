import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { usersApi } from '@/api/accounts'
import { consumablesApi } from '@/api/inventory'
import { assetModelsApi, locationsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import ConsumableListView from '@/views/inventory/ConsumableListView.vue'

import { button, chooseMenuEntry, click, menuEntries } from './dom'
import {
  bodyText,
  categoryRef,
  check,
  choose,
  hasField,
  locationRef,
  makeModel,
  modelRef,
  mountPage,
  page,
  pick,
  stubPickers,
  titled,
  type,
  userRef,
} from './inventoryHelpers'

function toner(overrides: Partial<Schemas['ConsumableOut']> = {}): Schemas['ConsumableOut'] {
  return {
    id: 's1',
    model: modelRef('Toner 207A', 'bulk', 'm5'),
    category: categoryRef('Printer supplies'),
    location: locationRef(),
    quantity: 12,
    reserved_quantity: 2,
    available_quantity: 10,
    min_quantity: 5,
    is_below_minimum: false,
    ...overrides,
  }
}

function movement(
  overrides: Partial<Schemas['ConsumableMovementOut']> = {},
): Schemas['ConsumableMovementOut'] {
  return {
    id: 'mv1',
    delta: 5,
    reason: 'receipt',
    note: '',
    recipient: null,
    created_at: '2026-10-01T09:00:00Z',
    ...overrides,
  } as Schemas['ConsumableMovementOut']
}

describe('ConsumableListView', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    stubPickers()
    vi.mocked(consumablesApi.list).mockResolvedValue(page([toner()]))
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  async function show(
    permissions: Record<string, 'read' | 'write'> = { consumables: 'write' },
    url = '/',
  ) {
    const result = await mountPage(ConsumableListView, {}, { permissions, url })
    unmount = () => result.wrapper.unmount()
    return result
  }

  /** Opens the row's "⋮" menu and picks `action`. */
  async function rowAction(action: string) {
    await click(titled('Actions')[0]!)
    await chooseMenuEntry(action)
  }

  it('lists stock with what is reserved and available', async () => {
    await show()
    const row = document.body.querySelector('tbody tr')!.textContent
    expect(row).toContain('Dell Toner 207A')
    expect(row).toContain('HQ / Main office')
    expect(row).toContain('12')
    expect(row).toContain('10')
  })

  it('books stock in', async () => {
    const move = vi.spyOn(consumablesApi, 'move').mockResolvedValue(toner({ quantity: 17 }))
    await show()
    await rowAction('Book in')
    expect(bodyText()).toContain('On hand: 12')
    expect(bodyText()).toContain('Change: +1')
    await type('Qty', '5')
    expect(bodyText()).toContain('Change: +5')
    await click('Save')

    expect(move).toHaveBeenCalledWith('s1', {
      delta: 5,
      reason: 'receipt',
      note: '',
      recipient: null,
    })
    // The list shows the new stock.
    expect(consumablesApi.list).toHaveBeenCalledTimes(2)
  })

  it('books stock out to a recipient', async () => {
    vi.mocked(usersApi.list).mockResolvedValue(page([userRef('Max Muster', 'u2') as never]))
    const move = vi.spyOn(consumablesApi, 'move').mockResolvedValue(toner())
    const { wrapper } = await show()
    await rowAction('Book out')
    expect(hasField('Recipient')).toBe(true)
    await type('Qty', '2')
    await pick(wrapper, usersApi.list, 'u2')
    await type('Notes', 'New hire')
    await click('Save')

    expect(move).toHaveBeenCalledWith('s1', {
      delta: -2,
      reason: 'issue',
      note: 'New hire',
      recipient: 'u2',
    })
  })

  it('corrects the count to what was counted', async () => {
    const move = vi.spyOn(consumablesApi, 'move').mockResolvedValue(toner())
    await show()
    await rowAction('Adjust')
    // Adjusting starts from the current count: nothing changes yet.
    expect(bodyText()).toContain('Change: 0')
    expect(button('Save').disabled).toBe(true)
    expect(hasField('Recipient')).toBe(false)
    await type('On hand', '9')
    expect(bodyText()).toContain('Change: -3')
    await click('Save')
    expect(move).toHaveBeenCalledWith(
      's1',
      expect.objectContaining({ delta: -3, reason: 'adjustment' }),
    )
  })

  it('starts over from one unit when switching from adjusting to booking', async () => {
    await show()
    await rowAction('Adjust')
    await choose('Book out')
    expect(bodyText()).toContain('Change: -1')
    expect(hasField('Recipient')).toBe(true)
  })

  it('shows the movements of an item', async () => {
    vi.spyOn(consumablesApi, 'movements').mockResolvedValue([
      movement(),
      movement({ id: 'mv2', delta: -1, reason: 'issue', recipient: userRef('Max Muster', 'u2') }),
      movement({ id: 'mv3', delta: -2, reason: 'adjustment', note: 'Stocktaking' }),
    ])
    await show()
    await rowAction('Movements')
    expect(consumablesApi.movements).toHaveBeenCalledWith('s1')
    const drawer = document.body.querySelector('.n-drawer')!.textContent
    expect(drawer).toContain('Movements · Dell Toner 207A')
    expect(drawer).toContain('+5')
    expect(drawer).toContain('Goods receipt')
    expect(drawer).toContain('Max Muster')
    expect(drawer).toContain('Stocktaking')
  })

  it('creates a new item once model and location are chosen', async () => {
    vi.mocked(assetModelsApi.list).mockResolvedValue(
      page([makeModel({ ...modelRef('Toner 207A', 'bulk', 'm5') })]),
    )
    vi.mocked(locationsApi.list).mockResolvedValue(page([locationRef() as never]))
    const create = vi.spyOn(consumablesApi, 'create').mockResolvedValue(toner())
    const { wrapper } = await show()
    await click('New consumable')
    expect(assetModelsApi.list).toHaveBeenCalledWith(expect.objectContaining({ tracking: 'bulk' }))
    expect(button('Save').disabled).toBe(true)
    await pick(wrapper, assetModelsApi.list, 'm5')
    expect(button('Save').disabled).toBe(true)
    // The second location picker: the first filters the list.
    await pick(wrapper, locationsApi.list, 'l1', 1)
    await type('Minimum', '4')
    await click('Save')
    expect(create).toHaveBeenCalledWith({ model: 'm5', location: 'l1', min_quantity: 4 })
  })

  it('only changes the minimum of an existing item', async () => {
    const update = vi.spyOn(consumablesApi, 'update').mockResolvedValue(toner())
    await show()
    await rowAction('Edit')
    await type('Minimum', '8')
    await click('Save')
    expect(update).toHaveBeenCalledWith('s1', { min_quantity: 8 })
  })

  it('narrows the list to items below their minimum', async () => {
    await show()
    expect(consumablesApi.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ below_minimum: null }),
    )
    await check('Only below minimum')
    expect(consumablesApi.list).toHaveBeenLastCalledWith(
      expect.objectContaining({ below_minimum: true }),
    )
  })

  it('starts narrowed when linked with ?below_minimum', async () => {
    await show({ consumables: 'write' }, '/x?below_minimum=1')
    expect(consumablesApi.list).toHaveBeenCalledWith(
      expect.objectContaining({ below_minimum: true }),
    )
  })

  it('hides creating items without the right to change consumables', async () => {
    await show({ consumables: 'read' })
    expect(bodyText()).not.toContain('New consumable')
  })

  it('offers read-only viewers no stock movements', async () => {
    await show({ consumables: 'read' })
    await click(titled('Actions')[0]!)
    expect(menuEntries()).not.toContain('Book in')
  })
})
