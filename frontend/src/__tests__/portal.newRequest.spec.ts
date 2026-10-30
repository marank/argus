import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
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
  requestItem,
  unmountPages,
} from './portalHelpers'

const api = vi.hoisted(() => ({
  catalog: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  availability: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  myConsumables: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  get: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  create: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
}))

vi.mock('@/api/requests', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/api/requests')>()
  return {
    ...original,
    portalApi: {
      ...original.portalApi,
      catalog: api.catalog,
      availability: api.availability,
      myConsumables: api.myConsumables,
    },
    requestsApi: { ...original.requestsApi, get: api.get, create: api.create },
  }
})

// Monday, 12 October 2026: the default period runs five days from today.
const TODAY = '2026-10-12'
const IN_FIVE_DAYS = '2026-10-16'

const T14 = catalogModel({ id: 'm-t14', full_name: 'ThinkPad T14' })
const AIR = catalogModel({ id: 'm-air', full_name: 'MacBook Air' })
const DOCK = catalogModel({ id: 'm-dock', full_name: 'USB-C Dock' })
const JABRA = catalogModel({ id: 'm-jabra', full_name: 'Jabra Evolve2' })
const INK = catalogModel({ id: 'm-ink', full_name: 'HP 305 ink' })
const VISIO = catalogModel({ id: 'm-visio', full_name: 'Visio Plan 2' })

/** Laptops with an accessory group below, a group with a single model, software, consumables. */
function catalog(): Schemas['CatalogCategoryOut'][] {
  return [
    catalogCategory({ id: 'c-laptops', name: 'Laptops', item_name: 'Laptop', models: [T14, AIR] }),
    catalogCategory({
      id: 'c-docks',
      name: 'Laptop accessories',
      parent_id: 'c-laptops',
      models: [DOCK],
    }),
    catalogCategory({ id: 'c-headsets', name: 'Headsets', models: [JABRA] }),
    catalogCategory({ id: 'c-ink', name: 'Ink', allow_any_model: false, models: [INK] }),
    catalogCategory({ id: 'c-software', name: 'Software', kind: 'software', models: [VISIO] }),
  ]
}

/** The same catalog as IT sees it: with what is free in the period. */
function catalogWithCounts(): Schemas['CatalogCategoryOut'][] {
  const counts = (available: number, reserved: number) => ({ available, reserved })
  return catalog().map((category) => ({
    ...category,
    ...counts(3, 0),
    models: category.models.map((model) => ({
      ...model,
      ...(model.id === 'm-air' ? counts(0, 2) : counts(3, 1)),
    })),
  }))
}

const EMPLOYEE = makeUser()
const IT_READER = makeUser({ is_it_staff: true, permissions: { requests: 'read' } })

async function open(options: { url?: string; user?: Schemas['CurrentUserOut'] } = {}) {
  return mountPage(NewRequestView, { url: options.url ?? '/portal/new', user: options.user })
}

/** The "Add" button in the row of an option. */
function addButtonOf(label: string): HTMLButtonElement {
  const row = [...document.body.querySelectorAll('.option')].find(
    (r) => r.querySelector('.label')?.textContent?.trim() === label,
  )
  if (!row) throw new Error(`no option "${label}"`)
  return row.querySelector('button')!
}

const cartLines = () =>
  [...document.body.querySelectorAll('.cart .lines li strong')].map((l) => l.textContent?.trim())

async function choosePurpose(text: string) {
  await typeInto(field('e.g. training, new hire, stocktaking'), text)
}

describe('NewRequestView', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 9, 12, 10, 0))
    Object.values(api).forEach((mock) => mock.mockReset())
    api.catalog.mockResolvedValue(catalog())
    api.myConsumables.mockResolvedValue([])
    api.create.mockResolvedValue(assetRequest({ id: 'r-new', number: 'R-2026-0100' }))
  })
  afterEach(() => {
    unmountPages()
    vi.useRealTimers()
  })

  describe('catalog', () => {
    it('asks for the catalog of the suggested period and opens the first group', async () => {
      await open()
      expect(api.catalog).toHaveBeenCalledWith({ start: TODAY, end: IN_FIVE_DAYS })
      const groups = [...document.body.querySelectorAll('.groups .name')].map((g) => g.textContent)
      // Accessory groups appear inside their parent, not as their own tile.
      expect(groups).toEqual(['Laptops', 'Headsets', 'Ink', 'Software', 'Something else'])
      expect(bodyText()).toContain('Laptop · any model')
      expect(bodyText()).toContain('Accessories: Laptop accessories')
      expect(bodyText()).toContain('USB-C Dock')
    })

    it('offers "any model" only where the group allows it and there is a choice', async () => {
      await open()
      await click(button('Headsets'))
      expect(bodyText()).toContain('Jabra Evolve2')
      expect(bodyText()).not.toContain('any model')
      await click(button('Ink'))
      expect(bodyText()).not.toContain('any model')
    })

    it('does not tell employees how many devices are free', async () => {
      await open({ user: EMPLOYEE })
      expect(bodyText()).not.toMatch(/available|reserved/)
      expect(bodyText()).not.toContain('Availability in the catalog refers to this period')
    })

    it('shows IT what is free and reserved in the period', async () => {
      api.catalog.mockResolvedValue(catalogWithCounts())
      await open({ user: IT_READER })
      const row = (label: string) => addButtonOf(label).closest('.option')!.textContent
      expect(row('ThinkPad T14')).toContain('3 available')
      expect(row('ThinkPad T14')).toContain('1 reserved')
      expect(row('MacBook Air')).toContain('not available')
      expect(row('MacBook Air')).toContain('2 reserved')
    })

    it('warns IT when a line asks for more than is free', async () => {
      api.catalog.mockResolvedValue(catalogWithCounts())
      await open({ user: IT_READER })
      await click(addButtonOf('MacBook Air'))
      expect(document.body.querySelector('.cart .warn')?.textContent).toContain('0 available')
    })

    it('refreshes the availability when IT changes the period', async () => {
      vi.useFakeTimers({ toFake: ['Date', 'setTimeout', 'clearTimeout'] })
      vi.setSystemTime(new Date(2026, 9, 12, 10, 0))
      api.catalog.mockResolvedValue(catalogWithCounts())
      api.availability.mockResolvedValue({
        categories: {},
        models: { 'm-air': { available: 4, reserved: 0 } },
      })
      await open({ user: IT_READER })
      document.body.querySelector<HTMLInputElement>('input[value="permanent"]')!.click()
      await vi.advanceTimersByTimeAsync(300)

      expect(api.availability).toHaveBeenLastCalledWith({ start: TODAY, permanent: true })
      const row = (label: string) => addButtonOf(label).closest('.option')!.textContent
      expect(row('MacBook Air')).toContain('4 available')
      // Not in the answer: nothing free.
      expect(row('ThinkPad T14')).toContain('not available')
    })

    it('searches models across all groups', async () => {
      await open()
      await typeInto(field('Search, e.g. headset'), 'dock')
      expect(bodyText()).toContain('Search results')
      expect(bodyText()).toContain('USB-C Dock')
      expect(bodyText()).not.toContain('ThinkPad T14')
    })

    it('offers a free-text request when the search finds nothing', async () => {
      await open()
      await typeInto(field('Search, e.g. headset'), 'beamer')
      expect(bodyText()).toContain('Nothing found for “beamer”.')
      expect(bodyText()).toContain('Item not in the catalog?')
      // The search term is taken over as the description.
      expect(field('Describe the device or item').value).toBe('beamer')
      await click(button('Add'))
      expect(cartLines()).toEqual(['beamer'])
    })

    it('adds consumables for the employee’s own devices from the quick pick', async () => {
      const printer = {
        id: 'a1',
        inventory_number: 'PRN-0007',
        model: {
          id: 'm-printer',
          name: 'OfficeJet',
          full_name: 'HP OfficeJet',
          designation: '',
          tracking: 'serialized',
        },
      } as const
      const ref = (id: string, name: string) => ({
        id,
        name,
        full_name: name,
        designation: '',
        tracking: 'bulk' as const,
      })
      api.myConsumables.mockResolvedValue([
        // The toner is not in the catalog, so it is not offered.
        { asset: printer, consumables: [ref('m-ink', 'HP 305 ink'), ref('m-toner', 'Toner')] },
      ] satisfies Schemas['MyConsumablesOut'][])
      await open()
      const quickPick = document.body.querySelector('.quick-pick')!
      expect(quickPick.textContent).toContain('For your devices')
      expect(quickPick.textContent).toContain('PRN-0007')
      expect(quickPick.textContent).not.toContain('Toner')

      await click(quickPick.querySelector('button.chip')!)
      expect(cartLines()).toEqual(['HP 305 ink'])
    })

    it('does not ask for the quick pick when it is switched off', async () => {
      const { wrapper } = await mountPage(NewRequestView, {
        url: '/portal/new',
        flags: { consumable_quick_pick: false },
      })
      expect(api.myConsumables).not.toHaveBeenCalled()
      expect(wrapper.find('.quick-pick').exists()).toBe(false)
    })
  })

  describe('building and submitting a request', () => {
    it('can only be submitted with a purpose and at least one line', async () => {
      await open()
      expect(bodyText()).toContain('Pick a category and add what you need.')
      expect(hasButton('Submit request')).toBe(false)

      await click(addButtonOf('ThinkPad T14'))
      expect(button('Submit request').disabled).toBe(true)
      await choosePurpose('   ')
      expect(button('Submit request').disabled).toBe(true)
      await choosePurpose('New hire')
      expect(button('Submit request').disabled).toBe(false)
    })

    it('adding an option twice raises its quantity instead of a second line', async () => {
      await open()
      await click(addButtonOf('MacBook Air'))
      await click(addButtonOf('MacBook Air'))
      expect(cartLines()).toEqual(['MacBook Air'])
      expect(addButtonOf('MacBook Air').closest('.option')!.textContent).toContain('2 in request')
    })

    it('removes a line from the request', async () => {
      await open()
      await click(addButtonOf('ThinkPad T14'))
      await click(addButtonOf('USB-C Dock'))
      await click(document.body.querySelector('.cart button[title="Remove"]')!)
      expect(cartLines()).toEqual(['USB-C Dock'])
    })

    it('sends a temporary request with models, "any model", free text, quantities and notes', async () => {
      const { router } = await open()
      await click(addButtonOf('Laptop · any model'))
      await click(addButtonOf('USB-C Dock'))
      await click(addButtonOf('USB-C Dock'))
      await typeInto(field('Describe the model or features you need'), '64 GB RAM')
      await click(button('Add'))
      expect(cartLines()).toEqual(['Laptop · any model', 'USB-C Dock', 'Laptops: 64 GB RAM'])
      expect(bodyText()).toContain('Custom request · IT will check')

      // A note for the first line.
      await click(document.body.querySelector('.cart .note-link')!)
      await typeInto(field('Note (optional)'), 'With US keyboard')
      await choosePurpose('Workshop in Munich')
      await typeInto(document.body.querySelector('.cart textarea')!, 'Room 4.12')
      await click(button('Submit request'))

      expect(api.create).toHaveBeenCalledWith({
        title: 'Workshop in Munich',
        notes: 'Room 4.12',
        duration: 'temporary',
        start_date: TODAY,
        end_date: IN_FIVE_DAYS,
        requested_pickup_date: TODAY,
        requester: null,
        follows: null,
        items: [
          {
            category: 'c-laptops',
            asset_model: null,
            description: '',
            quantity: 1,
            note: 'With US keyboard',
          },
          { category: null, asset_model: 'm-dock', description: '', quantity: 2, note: '' },
          {
            category: 'c-laptops',
            asset_model: null,
            description: '64 GB RAM',
            quantity: 1,
            note: '',
          },
        ],
      } satisfies Schemas['AssetRequestIn'])
      // Employees follow their request in the portal.
      expect(router.currentRoute.value.name).toBe('portal-request')
      expect(router.currentRoute.value.params.id).toBe('r-new')
      expect(router.currentRoute.value.query.created).toBe('1')
    })

    it('sends a permanent request without an end date', async () => {
      await open()
      document.body.querySelector<HTMLInputElement>('input[value="permanent"]')!.click()
      await flushPromises()
      expect(bodyText()).toContain('Needed from')
      await click(addButtonOf('ThinkPad T14'))
      await choosePurpose('Replacement')
      await click(button('Submit request'))
      expect(api.create).toHaveBeenCalledWith(
        expect.objectContaining({
          duration: 'permanent',
          start_date: TODAY,
          end_date: null,
          requested_pickup_date: TODAY,
        }),
      )
    })

    it('sends a request for something not in the catalog at all', async () => {
      await open()
      await click(button('Something else'))
      await typeInto(field('Describe the device or item'), 'Standing desk')
      await click(button('Add'))
      await choosePurpose('Back pain')
      await click(button('Submit request'))
      expect(api.create).toHaveBeenCalledWith(
        expect.objectContaining({
          items: [
            {
              category: null,
              asset_model: null,
              description: 'Standing desk',
              quantity: 1,
              note: '',
            },
          ],
        }),
      )
    })

    it('shows why the server refused the request and keeps what was entered', async () => {
      api.create.mockRejectedValue(new ApiError(400, 'The period is longer than allowed.'))
      const { router } = await open()
      await click(addButtonOf('ThinkPad T14'))
      await choosePurpose('Workshop')
      await click(button('Submit request'))

      expect(bodyText()).toContain('The period is longer than allowed.')
      expect(router.currentRoute.value.name).toBe('portal-new')
      expect(cartLines()).toEqual(['ThinkPad T14'])
      expect(field('e.g. training, new hire, stocktaking').value).toBe('Workshop')
      expect(button('Submit request').disabled).toBe(false)
    })

    it('takes IT to the request itself after submitting', async () => {
      const { router } = await open({ user: IT_READER })
      await click(addButtonOf('ThinkPad T14'))
      await choosePurpose('Loaner')
      await click(button('Submit request'))
      expect(bodyText()).toContain('Request R-2026-0100 submitted')
      expect(router.currentRoute.value.name).toBe('request')
      expect(router.currentRoute.value.params.id).toBe('r-new')
    })
  })

  describe('asking again', () => {
    const earlier = () =>
      assetRequest({
        id: 'r-old',
        number: 'R-2026-0007',
        title: 'Trade fair',
        notes: 'Booth 3',
        status: 'rejected',
        // Long past: the new period starts today and keeps the length (3 days).
        start_date: '2026-03-02',
        end_date: '2026-03-04',
        items: [
          requestItem({
            asset_model: {
              id: 'm-air',
              name: 'Air',
              full_name: 'MacBook Air',
              designation: '',
              tracking: 'serialized',
            },
            label: 'MacBook Air',
            quantity_requested: 2,
            note: 'Silver',
          }),
          requestItem({
            id: 'i2',
            asset_model: null,
            category: {
              id: 'c-laptops',
              name: 'Laptops',
              item_name: 'Laptop',
              code: 'NB',
              icon: 'laptop',
              kind: 'hardware',
            },
            description: 'Touchscreen',
            label: 'Laptops: Touchscreen',
          }),
        ],
      })

    it('prefills lines, details and period from the earlier request', async () => {
      api.get.mockResolvedValue(earlier())
      await open({ url: '/portal/new?from=r-old' })
      expect(api.get).toHaveBeenCalledWith('r-old')
      expect(bodyText()).toContain('Prefilled from R-2026-0007')
      expect(cartLines()).toEqual(['MacBook Air', 'Laptops: Touchscreen'])
      expect(field('e.g. training, new hire, stocktaking').value).toBe('Trade fair')
    })

    it('sends the new request as a follow-up of the earlier one', async () => {
      api.get.mockResolvedValue(earlier())
      await open({ url: '/portal/new?from=r-old' })
      await click(button('Submit request'))
      expect(api.create).toHaveBeenCalledWith({
        title: 'Trade fair',
        notes: 'Booth 3',
        duration: 'temporary',
        start_date: TODAY,
        end_date: '2026-10-14',
        requested_pickup_date: TODAY,
        requester: null,
        follows: 'r-old',
        items: [
          { category: null, asset_model: 'm-air', description: '', quantity: 2, note: 'Silver' },
          {
            category: 'c-laptops',
            asset_model: null,
            description: 'Touchscreen',
            quantity: 1,
            note: '',
          },
        ],
      } satisfies Schemas['AssetRequestIn'])
    })
  })
})
