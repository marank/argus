import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { NSelect } from 'naive-ui'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import AllocationPanel from '@/components/requests/AllocationPanel.vue'

import { buttons, click, typeInto } from './dom'
import {
  LAPTOP_CATEGORY,
  REQUEST_ID,
  device,
  makeItem,
  makeRequest,
  modal,
  mountWithApp,
  openModal,
  screen,
} from './requestsHelpers'

type AssetRequest = Schemas['AssetRequestOut']
type Item = Schemas['AssetRequestItemOut']

const api = vi.hoisted(() => {
  const fn = () => vi.fn<(...args: never[]) => Promise<unknown>>()
  return {
    requests: {
      candidates: fn(),
      allocate: fn(),
      autoAllocate: fn(),
      removeAllocation: fn(),
      resolveItem: fn(),
    },
    models: { list: fn(), create: fn() },
    manufacturers: { list: fn() },
    categories: { list: fn() },
  }
})

vi.mock('@/api/requests', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/requests')>()),
  requestsApi: api.requests,
}))
vi.mock('@/api/masterdata', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/masterdata')>()),
  assetModelsApi: api.models,
  manufacturersApi: api.manufacturers,
  categoriesApi: api.categories,
}))

const NO_CANDIDATES: Schemas['CandidatesOut'] = {
  assets: [],
  consumables: [],
  devices: [],
  licenses: [],
}

const DOCK: Schemas['AssetModelRefOut'] = {
  id: 'model-dock',
  name: 'Dock',
  designation: 'Dock',
  full_name: 'Acme Dock',
  tracking: 'serialized',
}

/** Picks an option of the n-th select on the page, as a click in its list would. */
function choose(wrapper: VueWrapper, index: number, value: string) {
  wrapper.findAllComponents(NSelect)[index]!.vm.$emit('update:value', value)
  return flushPromises()
}

/** Types (or scans) a code into the scan field and presses Enter. */
async function scan(code: string) {
  const input = document.body.querySelector<HTMLInputElement>('.scan-combobox input')!
  typeInto(input, code)
  await flushPromises()
  input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
  await flushPromises()
}

describe('AllocationPanel', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api.requests).forEach((mock) => mock.mockReset())
    api.requests.candidates.mockResolvedValue(NO_CANDIDATES)
    api.models.list.mockResolvedValue({ items: [], count: 0 })
    api.manufacturers.list.mockResolvedValue({ items: [], count: 0 })
    api.categories.list.mockResolvedValue({ items: [], count: 0 })
    api.models.create.mockReset()
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
  })

  async function panel(
    item: Item,
    { request = makeRequest({ status: 'confirmed', items: [item] }), editable = true } = {},
  ) {
    const updated = vi.fn<(r: AssetRequest) => void>()
    const result = await mountWithApp(AllocationPanel, {
      assetRequest: request,
      item,
      editable,
      availability: null,
      onUpdated: updated,
    })
    unmount = () => result.wrapper.unmount()
    return { ...result, updated }
  }

  const missingLaptop = () => makeItem({ quantity_requested: 2, quantity_confirmed: 2 })

  it('shows how much of the confirmed quantity is allocated and what was requested', async () => {
    await panel(
      makeItem({
        quantity_requested: 3,
        quantity_confirmed: 2,
        allocations: [device('INV-001', 'Laptop 14')],
      }),
    )
    const counts = document.body.querySelector('.counts')!.textContent!.replace(/\s+/g, ' ')
    expect(counts).toMatch(/1\s*\/\s*2/)
    expect(counts).toContain('(3)')
    expect(screen()).toContain('INV-001')
    expect(screen()).toContain('SN-INV-001')
  })

  it('looks for pool devices as soon as the item can take more', async () => {
    await panel(missingLaptop())
    expect(api.requests.candidates).toHaveBeenCalledWith('item-1', undefined)
  })

  it('offers no allocation tools outside preparation', async () => {
    await panel(missingLaptop(), { editable: false })
    expect(api.requests.candidates).not.toHaveBeenCalled()
    expect(buttons('Allocate automatically')).toEqual([])
  })

  it('allocates a scanned code on Enter', async () => {
    const after = makeRequest({ status: 'confirmed' })
    api.requests.allocate.mockResolvedValue(after)
    const { updated } = await panel(missingLaptop())
    await scan(' INV-007 ')

    expect(api.requests.allocate).toHaveBeenCalledWith(REQUEST_ID, {
      item: 'item-1',
      quantity: 1,
      code: 'INV-007',
    })
    expect(updated).toHaveBeenCalledWith(after)
    // The pool is asked again, as the device is no longer free. (Typing may also have
    // searched after its pause, so compare the order rather than count the calls.)
    expect(api.requests.candidates.mock.invocationCallOrder.at(-1)).toBeGreaterThan(
      api.requests.allocate.mock.invocationCallOrder[0]!,
    )
  })

  it('shows why a scanned code cannot be allocated', async () => {
    api.requests.allocate.mockRejectedValue(new ApiError(400, 'INV-007 is in repair.'))
    const { updated } = await panel(missingLaptop())
    await scan('INV-007')
    expect(screen()).toContain('INV-007 is in repair.')
    expect(updated).not.toHaveBeenCalled()
  })

  it('fills just this item automatically and says how many were taken', async () => {
    const after = makeRequest({ status: 'confirmed' })
    api.requests.autoAllocate.mockResolvedValue({ allocated: 2, asset_request: after })
    const { updated } = await panel(missingLaptop())
    await click('Allocate automatically')
    expect(api.requests.autoAllocate).toHaveBeenCalledWith(REQUEST_ID, 'item-1')
    expect(screen()).toContain('2 units allocated')
    expect(updated).toHaveBeenCalledWith(after)
  })

  it('allocates the chosen amount of a consumable', async () => {
    api.requests.candidates.mockResolvedValue({
      ...NO_CANDIDATES,
      consumables: [
        {
          id: 'cons-1',
          available_quantity: 10,
          model: { ...DOCK, id: 'model-mouse', full_name: 'Acme Mouse' },
          location: { id: 'loc-1', name: 'Store', full_name: 'HQ / Store' },
        },
      ],
    })
    api.requests.allocate.mockResolvedValue(makeRequest())
    await panel(makeItem({ quantity_requested: 5, quantity_confirmed: 5 }))
    expect(screen()).toContain('Acme Mouse · Store (10)')

    typeInto(document.body.querySelector('.consumable input'), '3')
    await flushPromises()
    await click('Allocate')
    expect(api.requests.allocate).toHaveBeenCalledWith(REQUEST_ID, {
      item: 'item-1',
      quantity: 3,
      consumable: 'cons-1',
    })
  })

  it('removes an allocation that was not handed out yet', async () => {
    const after = makeRequest({ status: 'confirmed' })
    api.requests.removeAllocation.mockResolvedValue(after)
    const { updated } = await panel(
      makeItem({ quantity_confirmed: 1, allocations: [device('INV-001', 'Laptop 14')] }),
    )
    document.body.querySelector<HTMLButtonElement>('button[title="Remove"]')!.click()
    await flushPromises()
    expect(api.requests.removeAllocation).toHaveBeenCalledWith(REQUEST_ID, 'alloc-INV-001')
    expect(updated).toHaveBeenCalledWith(after)
  })

  it('lets IT still swap devices of a ready request, but not handed-out ones', async () => {
    const item = makeItem({
      quantity_requested: 2,
      quantity_confirmed: 2,
      allocations: [
        device('INV-001', 'Laptop 14'),
        device('INV-002', 'Laptop 14', { handed_out_at: '2026-11-02T09:00:00Z' }),
      ],
    })
    await panel(item, { request: makeRequest({ status: 'ready', items: [item] }), editable: false })
    expect(document.body.querySelectorAll('button[title="Remove"]')).toHaveLength(1)
    expect(screen()).toContain('handed out')
  })

  it('marks returned devices by the state they came back in', async () => {
    const item = makeItem({
      quantity_requested: 2,
      quantity_confirmed: 2,
      allocations: [
        device('INV-001', 'Laptop 14', { returned_at: '2026-11-05T10:00:00Z' }),
        device('INV-002', 'Laptop 14', {
          returned_at: '2026-11-05T10:00:00Z',
          returned_damaged: true,
        }),
      ],
    })
    await panel(item, {
      request: makeRequest({ status: 'completed', items: [item] }),
      editable: false,
    })
    const states = [...document.body.querySelectorAll('.state')].map((s) => s.textContent?.trim())
    expect(states).toEqual(['In stock', 'In repair'])
    expect(document.body.querySelector('button[title="Remove"]')).toBeNull()
  })

  describe('software', () => {
    const software = () =>
      makeItem({ is_software: true, asset_model: null, label: 'Office 365', quantity_confirmed: 1 })

    it('assigns a seat of a personal license', async () => {
      api.requests.candidates.mockResolvedValue({
        ...NO_CANDIDATES,
        licenses: [
          {
            id: 'lic-1',
            assign_to: 'user',
            free_seats: 4,
            reference: 'EA-2026',
            valid_until: null,
            model: { ...DOCK, id: 'model-o365', full_name: 'Office 365' },
          },
        ],
      })
      api.requests.allocate.mockResolvedValue(makeRequest())
      const { wrapper } = await panel(software())
      wrapper.findComponent(NSelect).vm.$emit('focus')
      await flushPromises()
      expect(
        (wrapper.findComponent(NSelect).props('options') as { label: string }[])[0]!.label,
      ).toBe('Office 365 (EA-2026) · 4 free')

      await choose(wrapper, 0, 'lic-1')
      await click('Assign seat')
      expect(api.requests.allocate).toHaveBeenCalledWith(REQUEST_ID, {
        item: 'item-1',
        quantity: 1,
        license: 'lic-1',
      })
    })

    it('asks for the employee’s device before assigning a device license', async () => {
      api.requests.candidates.mockResolvedValue({
        ...NO_CANDIDATES,
        licenses: [
          {
            id: 'lic-2',
            assign_to: 'device',
            free_seats: 1,
            reference: '',
            valid_until: null,
            model: { ...DOCK, id: 'model-cad', full_name: 'CAD Suite' },
          },
        ],
        devices: [device('INV-009', 'Laptop 14').asset!],
      })
      api.requests.allocate.mockResolvedValue(makeRequest())
      const { wrapper } = await panel(software())
      wrapper.findComponent(NSelect).vm.$emit('focus')
      await flushPromises()

      await choose(wrapper, 0, 'lic-2')
      expect(buttons('Assign seat')[0]!.disabled).toBe(true)
      await choose(wrapper, 1, 'asset-INV-009')
      await click('Assign seat')
      expect(api.requests.allocate).toHaveBeenCalledWith(REQUEST_ID, {
        item: 'item-1',
        quantity: 1,
        license: 'lic-2',
        asset: 'asset-INV-009',
      })
    })

    it('points to the licenses when no seat is free', async () => {
      const { wrapper } = await panel(software())
      wrapper.findComponent(NSelect).vm.$emit('focus')
      await flushPromises()
      expect(screen()).toContain('No free license. Add a license or more seats:')
      expect(screen()).toContain('Open licenses')
    })
  })

  describe('a free-text line', () => {
    const freeText = () =>
      makeItem({
        id: 'item-ft',
        is_free_text: true,
        asset_model: null,
        category: LAPTOP_CATEGORY,
        description: 'Docking station USB-C',
        label: 'Laptops: Docking station USB-C',
      })

    /** Picks the manufacturer in the new model form. */
    function chooseManufacturer(wrapper: VueWrapper, id: string) {
      const select = wrapper
        .findAllComponents(EntitySelect)
        .find((s) => (s.props() as { fetcher: unknown }).fetcher === api.manufacturers.list)!
      select.findComponent(NSelect).vm.$emit('update:value', id)
    }

    async function freeTextPanel(status: AssetRequest['status'] = 'submitted') {
      const item = freeText()
      return panel(item, { request: makeRequest({ status, items: [item] }), editable: false })
    }

    it('asks IT to resolve it while the request is open', async () => {
      await freeTextPanel()
      expect(screen()).toContain('Custom request')
      expect(screen()).toContain('Not in the catalog: create a model, assign an existing one')
      expect(api.models.list).toHaveBeenCalledWith(
        expect.objectContaining({ category: 'cat-laptop', is_active: true }),
      )
    })

    it('is no longer resolvable once the devices are handed out', async () => {
      await freeTextPanel('handed_out')
      expect(screen()).not.toContain('Not in the catalog')
    })

    it('maps the line to an existing model', async () => {
      api.models.list.mockResolvedValue({ items: [{ ...DOCK, category: {} }], count: 1 })
      const after = makeRequest()
      api.requests.resolveItem.mockResolvedValue(after)
      const { wrapper, updated } = await freeTextPanel()
      expect(buttons('Assign')[0]!.disabled).toBe(true)

      await choose(wrapper, 0, 'model-dock')
      await click('Assign')
      expect(api.requests.resolveItem).toHaveBeenCalledWith(REQUEST_ID, 'item-ft', 'model-dock')
      expect(updated).toHaveBeenCalledWith(after)
    })

    it('creates a model from the description and assigns it', async () => {
      api.manufacturers.list.mockResolvedValue({ items: [{ id: 'man-1', name: 'Acme' }], count: 1 })
      api.models.create.mockResolvedValue({ id: 'model-new' })
      const after = makeRequest()
      api.requests.resolveItem.mockResolvedValue(after)
      const { wrapper, updated } = await freeTextPanel()

      await click('Create model')
      const inputs = openModal().querySelectorAll<HTMLInputElement>('input.n-input__input-el')
      expect(inputs[0]!.value).toBe('Docking station USB-C')
      expect(inputs[1]!.value).toBe('Docking station USB-C')
      // The manufacturer is required; the category comes from the line.
      expect(buttons('Create and assign')[0]!.disabled).toBe(true)

      chooseManufacturer(wrapper, 'man-1')
      typeInto(inputs[0], 'USB-C Dock')
      await flushPromises()
      await click('Create and assign')

      expect(api.models.create).toHaveBeenCalledWith(
        expect.objectContaining({
          name: 'USB-C Dock',
          designation: 'Docking station USB-C',
          manufacturer: 'man-1',
          category: 'cat-laptop',
          tracking: 'serialized',
        }),
      )
      expect(api.requests.resolveItem).toHaveBeenCalledWith(REQUEST_ID, 'item-ft', 'model-new')
      expect(updated).toHaveBeenCalledWith(after)
      expect(modal()).toBeNull()
    })

    it('keeps the new model form open when the model cannot be created', async () => {
      api.manufacturers.list.mockResolvedValue({ items: [{ id: 'man-1', name: 'Acme' }], count: 1 })
      api.models.create.mockRejectedValue(new ApiError(400, 'A model with this name exists.'))
      const { wrapper } = await freeTextPanel()
      await click('Create model')
      chooseManufacturer(wrapper, 'man-1')
      await flushPromises()
      await click('Create and assign')

      expect(screen()).toContain('A model with this name exists.')
      expect(api.requests.resolveItem).not.toHaveBeenCalled()
      expect(openModal().textContent).toContain('Create model from request')
    })
  })
})
