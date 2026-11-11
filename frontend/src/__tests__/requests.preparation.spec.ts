import { flushPromises, type VueWrapper } from '@vue/test-utils'
import { NSelect } from 'naive-ui'
import { afterEach, beforeEach, describe, expect, it, onTestFinished, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import ScanCombobox from '@/components/common/ScanCombobox.vue'
import PreparationLine from '@/components/requests/preparation/PreparationLine.vue'
import PreparationPanel from '@/components/requests/preparation/PreparationPanel.vue'

import { buttons, click, typeInto } from './dom'
import {
  LAPTOP_CATEGORY,
  REQUEST_ID,
  device,
  makeAllocation,
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
      lineCandidates: fn(),
      scan: fn(),
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

const MODEL = (
  id: string,
  fullName: string,
  tracking: Schemas['AssetModelRefOut']['tracking'],
) => ({
  id,
  name: fullName,
  designation: fullName,
  full_name: fullName,
  tracking,
})

const stock = (id: string, location: string, available: number) => ({
  id,
  available_quantity: available,
  model: MODEL('model-cable', 'USB-C cable', 'bulk'),
  location: { id: `loc-${id}`, name: location, full_name: location },
})

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

const rows = () => [...document.body.querySelectorAll('.row')]
const rowTexts = () => rows().map((r) => r.textContent!.replace(/\s+/g, ' ').trim())

describe('PreparationPanel', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api.requests).forEach((mock) => mock.mockReset())
    api.requests.candidates.mockResolvedValue(NO_CANDIDATES)
    api.requests.lineCandidates.mockResolvedValue({
      matches: [],
      pool: [{ item: 'item-1', available: 3 }],
    })
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
    items: Item[],
    { request = makeRequest({ status: 'confirmed', items }), editable = true } = {},
  ) {
    const updated = vi.fn<(r: AssetRequest) => void>()
    const result = await mountWithApp(PreparationPanel, {
      assetRequest: request,
      editable,
      availability: () => null,
      onUpdated: updated,
    })
    unmount = () => result.wrapper.unmount()
    return { ...result, updated }
  }

  const missingLaptops = (overrides: Partial<Item> = {}) =>
    makeItem({ quantity_requested: 2, quantity_confirmed: 2, ...overrides })

  it('builds a row per unit alike: category, model, numbers, and a dashed one for each open unit', async () => {
    await panel([
      makeItem({
        quantity_requested: 3,
        quantity_confirmed: 2,
        allocations: [device('INV-001', 'Laptop 14')],
      }),
    ])
    const counts = document.body.querySelector('.count')!.textContent!.replace(/\s+/g, ' ')
    expect(counts).toMatch(/1\s*\/\s*2/)
    expect(counts).toContain('(3)')
    expect(rowTexts()).toEqual([
      'Laptops · Acme Laptop 14 · INV-001 · SN-INV-001',
      'Acme Laptop 14 · open',
    ])
    expect(document.body.querySelectorAll('.row.open')).toHaveLength(1)
    expect(screen()).toContain('1 of 2 ready')
  })

  it('only shows what the request holds outside preparation', async () => {
    await panel([missingLaptops()], { editable: false })
    expect(document.body.querySelector('.scan-combobox')).toBeNull()
    expect(buttons('Automatically')).toEqual([])
    expect(api.requests.lineCandidates).not.toHaveBeenCalled()
  })

  it('puts a scanned device in the line it fits and shows where it went', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    onTestFinished(() => {
      vi.useRealTimers()
    })
    const after = makeRequest({
      status: 'confirmed',
      items: [missingLaptops({ allocations: [device('INV-007', 'Laptop 14')] })],
    })
    api.requests.scan.mockResolvedValue(after)
    const { updated, wrapper } = await panel([missingLaptops()])
    await scan(' INV-007 ')

    expect(api.requests.scan).toHaveBeenCalledWith(REQUEST_ID, { code: 'INV-007' })
    expect(updated).toHaveBeenCalledWith(after)
    expect(screen()).toContain('INV-007 → Acme Laptop 14')
    // The new row is highlighted once the page shows the updated request.
    expect(wrapper.findComponent(PreparationLine).props('highlight')).toBe('alloc-INV-007')
    // ... for a moment only.
    vi.advanceTimersByTime(3000)
    await flushPromises()
    expect(wrapper.findComponent(PreparationLine).props('highlight')).toBeNull()
  })

  it('lists pool devices while typing, with the line each would go to', async () => {
    api.requests.lineCandidates.mockImplementation((async (_id: string, q?: string) => ({
      matches: q
        ? [
            {
              item: 'item-1',
              asset: {
                id: 'asset-9',
                inventory_number: 'INV-009',
                serial_number: 'SN-9',
                condition: 'new',
                model: MODEL('m1', 'Acme Laptop 14', 'serialized'),
                location: null,
              },
            },
          ]
        : [],
      pool: [{ item: 'item-1', available: 3 }],
    })) as never)
    api.requests.scan.mockResolvedValue(makeRequest())
    const { wrapper } = await panel([missingLaptops()])
    const combobox = wrapper.findComponent(ScanCombobox)
    // Nothing searched yet: no "nothing found".
    expect(combobox.props('emptyText')).toBeUndefined()
    combobox.vm.$emit('search', 'INV')
    await flushPromises()
    expect(api.requests.lineCandidates).toHaveBeenLastCalledWith(REQUEST_ID, 'INV')
    const options = combobox.props('options') as { value: string }[]
    expect(options.map((o) => o.value)).toEqual(['asset-9'])
    const hit = combobox.props('renderLabel')!({ value: 'asset-9' })
    expect(JSON.stringify(hit)).toContain('→ Acme Laptop 14')

    combobox.vm.$emit('search', 'XYZ')
    await flushPromises()
    expect(combobox.props('emptyText')).toContain('No matching device')

    combobox.vm.$emit('select', 'asset-9')
    await flushPromises()
    expect(api.requests.scan).toHaveBeenCalledWith(REQUEST_ID, { asset: 'asset-9' })
  })

  it('shows why a scanned code cannot be allocated', async () => {
    api.requests.scan.mockRejectedValue(new ApiError(400, 'INV-007 is in repair.'))
    const { updated } = await panel([missingLaptops()])
    await scan('INV-007')
    expect(screen()).toContain('INV-007 is in repair.')
    expect(updated).not.toHaveBeenCalled()
  })

  it('fills a line automatically from its header and says how many were taken', async () => {
    const after = makeRequest({ status: 'confirmed' })
    api.requests.autoAllocate.mockResolvedValue({ allocated: 2, asset_request: after })
    const { updated } = await panel([missingLaptops()])
    // One line: no "all" next to the progress.
    expect(buttons('Allocate all automatically')).toEqual([])
    await click('Automatically')
    expect(api.requests.autoAllocate).toHaveBeenCalledWith(REQUEST_ID, 'item-1')
    expect(screen()).toContain('2 units allocated')
    expect(updated).toHaveBeenCalledWith(after)
  })

  it('offers no automatic filling for a line the pool has nothing for', async () => {
    api.requests.lineCandidates.mockResolvedValue({ matches: [], pool: [] })
    await panel([missingLaptops()])
    expect(buttons('Automatically')).toEqual([])
  })

  it('fills all lines at once when several are open', async () => {
    api.requests.lineCandidates.mockResolvedValue({
      matches: [],
      pool: [
        { item: 'item-1', available: 3 },
        { item: 'item-2', available: 1 },
      ],
    })
    api.requests.autoAllocate.mockResolvedValue({ allocated: 3, asset_request: makeRequest() })
    await panel([missingLaptops(), missingLaptops({ id: 'item-2', label: 'Acme Dock' })])
    await click('Allocate all automatically')
    expect(api.requests.autoAllocate).toHaveBeenCalledWith(REQUEST_ID)
  })

  it('removes an allocation with its round button', async () => {
    const after = makeRequest({ status: 'confirmed' })
    api.requests.removeAllocation.mockResolvedValue(after)
    const { updated } = await panel([
      missingLaptops({ allocations: [device('INV-001', 'Laptop 14')] }),
    ])
    document.body.querySelector<HTMLButtonElement>('button[title="Remove"]')!.click()
    await flushPromises()
    expect(api.requests.removeAllocation).toHaveBeenCalledWith(REQUEST_ID, 'alloc-INV-001')
    expect(updated).toHaveBeenCalledWith(after)
  })

  it('folds a finished line to its header until it is opened', async () => {
    await panel([
      makeItem({ quantity_confirmed: 1, allocations: [device('INV-001', 'Laptop 14')] }),
      missingLaptops({ id: 'item-2' }),
    ])
    expect(rowTexts().some((t) => t.includes('INV-001'))).toBe(false)
    ;(document.body.querySelector('.head.foldable') as HTMLElement).click()
    await flushPromises()
    expect(rowTexts().some((t) => t.includes('INV-001'))).toBe(true)
  })

  it('lets IT still swap devices of a ready request, but not handed-out ones', async () => {
    const item = missingLaptops({
      allocations: [
        device('INV-001', 'Laptop 14'),
        device('INV-002', 'Laptop 14', { handed_out_at: '2026-11-02T09:00:00Z' }),
      ],
    })
    await panel([item], {
      request: makeRequest({ status: 'ready', items: [item] }),
      editable: false,
    })
    expect(document.body.querySelectorAll('button[title="Remove"]')).toHaveLength(1)
    expect(screen()).toContain('handed out')
  })

  it('marks returned devices by the state they came back in', async () => {
    const item = missingLaptops({
      allocations: [
        device('INV-001', 'Laptop 14', { returned_at: '2026-11-05T10:00:00Z' }),
        device('INV-002', 'Laptop 14', {
          returned_at: '2026-11-05T10:00:00Z',
          returned_damaged: true,
        }),
      ],
    })
    await panel([item], {
      request: makeRequest({ status: 'completed', items: [item] }),
      editable: false,
    })
    expect(rowTexts()[0]).toContain('In stock')
    expect(rowTexts()[1]).toContain('In repair')
    expect(document.body.querySelector('button[title="Remove"]')).toBeNull()
  })

  describe('consumables', () => {
    const cables = (overrides: Partial<Item> = {}) =>
      makeItem({
        asset_model: MODEL('model-cable', 'USB-C cable', 'bulk'),
        label: 'USB-C cable',
        category_name: 'Cables',
        quantity_requested: 5,
        quantity_confirmed: 5,
        ...overrides,
      })
    const tick = () =>
      document.body.querySelector<HTMLButtonElement>('button[title="Tick off as set aside"]')!

    it('are ticked off from the one place holding enough', async () => {
      api.requests.candidates.mockResolvedValue({
        ...NO_CANDIDATES,
        consumables: [stock('c1', 'Store', 10), stock('c2', 'Basement', 2)],
      })
      api.requests.allocate.mockResolvedValue(makeRequest())
      await panel([cables()])
      expect(rowTexts()).toEqual(['Cables · 5× USB-C cable'])
      tick().click()
      await flushPromises()
      expect(api.requests.allocate).toHaveBeenCalledWith(REQUEST_ID, {
        item: 'item-1',
        consumable: 'c1',
        quantity: 5,
      })
    })

    it('ask where to take them from when several places hold enough', async () => {
      api.requests.candidates.mockResolvedValue({
        ...NO_CANDIDATES,
        consumables: [stock('c1', 'Store', 10), stock('c2', 'Basement', 8)],
      })
      api.requests.allocate.mockResolvedValue(makeRequest())
      await panel([cables()])
      tick().click()
      await flushPromises()
      expect(screen()).toContain('Store (10)')
      expect(screen()).toContain('Basement (8)')
      ;[...document.body.querySelectorAll<HTMLElement>('.n-dropdown-option-body')]
        .find((o) => o.textContent?.includes('Basement'))!
        .click()
      await flushPromises()
      expect(api.requests.allocate).toHaveBeenCalledWith(REQUEST_ID, {
        item: 'item-1',
        consumable: 'c2',
        quantity: 5,
      })
    })

    it('say so when no place holds enough', async () => {
      api.requests.candidates.mockResolvedValue({
        ...NO_CANDIDATES,
        consumables: [stock('c1', 'Store', 3)],
      })
      await panel([cables()])
      tick().click()
      await flushPromises()
      expect(screen()).toContain('Not enough in stock: 5 needed in one place.')
      expect(api.requests.allocate).not.toHaveBeenCalled()
    })

    it('lose their tick by removing what was set aside', async () => {
      const after = makeRequest()
      api.requests.removeAllocation.mockResolvedValue(after)
      const item = cables({
        allocations: [
          makeAllocation({ id: 'a1', quantity: 3, consumable: stock('c1', 'Store', 7) as never }),
          makeAllocation({
            id: 'a2',
            quantity: 2,
            consumable: stock('c2', 'Basement', 6) as never,
          }),
        ],
      })
      const { updated } = await panel([item, missingLaptops({ id: 'item-2' })])
      ;(document.body.querySelector('.head.foldable') as HTMLElement).click()
      await flushPromises()
      expect(rowTexts()[0]).toContain('from Store, Basement')
      document.body.querySelector<HTMLButtonElement>('button[title="Remove the tick"]')!.click()
      await flushPromises()
      expect(api.requests.removeAllocation.mock.calls).toEqual([
        [REQUEST_ID, 'a1'],
        [REQUEST_ID, 'a2'],
      ])
      expect(updated).toHaveBeenCalledWith(after)
    })
  })

  describe('software', () => {
    const software = () =>
      makeItem({
        is_software: true,
        asset_model: null,
        label: 'Office 365',
        category_name: 'Software',
        quantity_confirmed: 1,
      })
    const license = (id: string, assignTo: 'user' | 'device', name: string) => ({
      id,
      assign_to: assignTo,
      free_seats: 4,
      reference: id === 'lic-1' ? 'EA-2026' : '',
      valid_until: null,
      model: MODEL(`model-${id}`, name, 'license'),
    })

    it('assigns a seat of a personal license as soon as it is picked', async () => {
      api.requests.candidates.mockResolvedValue({
        ...NO_CANDIDATES,
        licenses: [license('lic-1', 'user', 'Office 365')],
      })
      api.requests.allocate.mockResolvedValue(makeRequest())
      const { wrapper } = await panel([software()])
      wrapper.findComponent(NSelect).vm.$emit('focus')
      await flushPromises()
      expect(
        (wrapper.findComponent(NSelect).props('options') as { label: string }[])[0]!.label,
      ).toBe('Office 365 (EA-2026) · 4 free')

      await choose(wrapper, 0, 'lic-1')
      expect(api.requests.allocate).toHaveBeenCalledWith(REQUEST_ID, {
        item: 'item-1',
        quantity: 1,
        license: 'lic-1',
      })
    })

    it('asks for the employee’s device before assigning a device license', async () => {
      api.requests.candidates.mockResolvedValue({
        ...NO_CANDIDATES,
        licenses: [license('lic-2', 'device', 'CAD Suite')],
        devices: [device('INV-009', 'Laptop 14').asset!],
      })
      api.requests.allocate.mockResolvedValue(makeRequest())
      const { wrapper } = await panel([software()])
      wrapper.findComponent(NSelect).vm.$emit('focus')
      await flushPromises()

      await choose(wrapper, 0, 'lic-2')
      expect(api.requests.allocate).not.toHaveBeenCalled()
      await choose(wrapper, 1, 'asset-INV-009')
      expect(api.requests.allocate).toHaveBeenCalledWith(REQUEST_ID, {
        item: 'item-1',
        quantity: 1,
        license: 'lic-2',
        asset: 'asset-INV-009',
      })
    })

    it('points to the licenses when no seat is free', async () => {
      const { wrapper } = await panel([software()])
      wrapper.findComponent(NSelect).vm.$emit('focus')
      await flushPromises()
      expect(screen()).toContain('No free license. Add a license or more seats:')
      expect(screen()).toContain('Open licenses')
    })

    it('names whose seat it is', async () => {
      const item = { ...software(), quantity_missing: 0, quantity_allocated: 1 }
      item.allocations = [
        makeAllocation({
          license: {
            id: 'lic-1',
            model: MODEL('m', 'Office 365', 'license'),
            device: null,
            reference: '',
            valid_until: null,
          },
        }),
      ]
      await panel([item], {
        request: makeRequest({ status: 'ready', items: [item] }),
        editable: false,
      })
      expect(rowTexts()[0]).toBe('Software · Office 365 · seat for Jane Doe')
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
      return panel([item], { request: makeRequest({ status, items: [item] }), editable: false })
    }

    it('asks IT to resolve it while the request is open, with its units locked', async () => {
      await freeTextPanel()
      expect(screen()).toContain('Custom request')
      expect(screen()).toContain('Not in the catalog: create a model, assign an existing one')
      expect(document.body.querySelector('.row.locked')!.textContent).toContain('set a model first')
      expect(api.models.list).toHaveBeenCalledWith(
        expect.objectContaining({ category: 'cat-laptop', is_active: true }),
      )
    })

    it('is no longer resolvable once the devices are handed out', async () => {
      await freeTextPanel('handed_out')
      expect(screen()).not.toContain('Not in the catalog')
    })

    it('maps the line to an existing model', async () => {
      api.models.list.mockResolvedValue({
        items: [{ ...MODEL('model-dock', 'Acme Dock', 'serialized'), category: {} }],
        count: 1,
      })
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
