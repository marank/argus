import { flushPromises, mount } from '@vue/test-utils'
import { NDialogProvider, NMessageProvider } from 'naive-ui'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { createMemoryHistory, createRouter, RouterView } from 'vue-router'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import ErrorPopover from '@/components/common/ErrorPopover.vue'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import NewRequestView from '@/views/portal/NewRequestView.vue'

import { makeUser } from './helpers'
import { button, click, fakeMatchMedia, typeInto } from './dom'
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
      holds_accessories: true,
      models: [DOCK],
    }),
    catalogCategory({ id: 'c-headsets', name: 'Headsets', models: [JABRA] }),
    catalogCategory({ id: 'c-ink', name: 'Ink', model_choice: 'specific_only', models: [INK] }),
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

function optionRow(label: string): Element {
  const row = [...document.body.querySelectorAll('.option')].find(
    (r) => r.querySelector('.label')?.textContent?.trim() === label,
  )
  if (!row) throw new Error(`no option "${label}"`)
  return row
}

/** The "Add" button in the row of an option (the plus of its stepper once added). */
const addButtonOf = (label: string) => optionRow(label).querySelector<HTMLButtonElement>('.add')!

const cartLines = () =>
  [...document.body.querySelectorAll('.cart .lines li strong')].map((l) => l.textContent?.trim())

async function choosePurpose(text: string) {
  await typeInto(field('e.g. training, new hire, stocktaking'), text)
}

/** Step 1 with a purpose, then on to the selection. */
async function toSelection(purpose = 'Workshop') {
  await choosePurpose(purpose)
  await click(button('On to selection'))
}

/** Shown unless the element or a parent is hidden with v-show. */
function visible(selector: string) {
  let element = document.body.querySelector<HTMLElement>(selector)
  if (!element) return false
  for (; element; element = element.parentElement)
    if (element.style.display === 'none') return false
  return true
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

  describe('steps', () => {
    it('walks from the details to the selection, with the cart docked beside both', async () => {
      await open()
      expect(visible('.details-card')).toBe(true)
      expect(visible('.browser')).toBe(false)
      expect(visible('.cart-panel')).toBe(true)

      // Without a purpose the button says what is missing instead of being dead.
      await click(button('On to selection'))
      expect(visible('.browser')).toBe(false)
      expect(document.body.querySelector('.details-card .error')?.textContent).toContain(
        'Please enter a purpose',
      )

      await toSelection('New hire')
      expect(visible('.details-card')).toBe(false)
      expect(visible('.browser')).toBe(true)
      await click(addButtonOf('ThinkPad T14'))
      expect(cartLines()).toEqual(['ThinkPad T14'])
      // The panel repeats the details and sends from its foot.
      expect(document.body.querySelector('.cart-panel .summary')!.textContent).toContain('New hire')
      expect(button('Submit request').disabled).toBe(false)
    })

    it('leads back to the details from the trail and from the cart', async () => {
      await open()
      await toSelection()
      await click(button('1 · Details'))
      expect(visible('.details-card')).toBe(true)
      // The summary belongs to the selection step only.
      expect(document.body.querySelector('.cart-panel .summary')).toBeNull()

      await click(button('On to selection'))
      await click(document.body.querySelector<HTMLElement>('.cart-panel .summary')!)
      expect(visible('.details-card')).toBe(true)

      // And from a button of its own next to the X.
      await click(button('On to selection'))
      await click(document.body.querySelector<HTMLElement>('.head-back')!)
      expect(visible('.details-card')).toBe(true)
      expect(document.body.querySelector('.head-back')).toBeNull()
    })

    it("has the selection in the browser's history: back leads to the details", async () => {
      const { router } = await open()
      await toSelection()
      expect(router.currentRoute.value.query.step).toBe('catalog')
      router.back()
      await flushPromises()
      expect(router.currentRoute.value.name).toBe('portal-new')
      expect(visible('.details-card')).toBe(true)
    })

    it('goes on with Enter in the purpose', async () => {
      await open()
      const purpose = field('e.g. training, new hire, stocktaking')
      await typeInto(purpose, 'Workshop')
      purpose.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
      await flushPromises()
      expect(visible('.browser')).toBe(true)
    })

    it('keeps the way to sending in sight where the cart does not fit beside the catalog', async () => {
      const restore = fakeMatchMedia(1000)
      try {
        await open()
        expect(document.body.querySelector('.cart-dock')).toBeNull()
        await toSelection()
        await click(addButtonOf('ThinkPad T14'))
        const review = document.body.querySelector<HTMLElement>('.cart-bar-button')!
        expect(review.textContent).toContain('1')
        expect(review.textContent).toContain('Review and send')

        await click(review)
        expect(cartLines()).toEqual(['ThinkPad T14'])
        await click(document.body.querySelector<HTMLElement>('.panel-close')!)
        expect(visible('.cart-panel')).toBe(false)
      } finally {
        restore()
      }
    })
  })

  describe('stepper', () => {
    it('counts an option up and down right in the catalog', async () => {
      await open()
      expect(optionRow('MacBook Air').querySelector('.in-cart')?.textContent).toBe('0')
      await click(addButtonOf('MacBook Air'))
      await click(addButtonOf('MacBook Air'))
      const count = () => optionRow('MacBook Air').querySelector('.in-cart')?.textContent
      expect(count()).toBe('2')
      expect(cartLines()).toEqual(['MacBook Air'])

      await click(optionRow('MacBook Air').querySelector<HTMLElement>('.less')!)
      expect(count()).toBe('1')
      // At none the line goes; the stepper stays, at 0 with nothing to take away.
      await click(optionRow('MacBook Air').querySelector<HTMLElement>('.less')!)
      expect(cartLines()).toEqual([])
      expect(count()).toBe('0')
      expect(optionRow('MacBook Air').querySelector<HTMLButtonElement>('.less')!.disabled).toBe(
        true,
      )
    })
  })

  describe('on a phone', () => {
    const original = window.matchMedia
    beforeEach(() => {
      window.matchMedia = ((query: string) => ({
        matches: query.includes('max-width'),
        media: query,
        addEventListener: () => undefined,
        removeEventListener: () => undefined,
      })) as unknown as typeof window.matchMedia
    })
    afterEach(() => {
      window.matchMedia = original
    })

    it('shows the selection as a menu: groups, then one group, back to the groups', async () => {
      await open()
      await toSelection()
      expect(visible('.groups')).toBe(true)
      expect(visible('.options')).toBe(false)

      await click(button('Headsets'))
      expect(visible('.groups')).toBe(false)
      expect(visible('.options')).toBe(true)
      expect(document.body.querySelector('.head-title')?.textContent).toBe('Headsets')

      // Back closes the group first, then leaves the step.
      await click(button('Back'))
      expect(visible('.groups')).toBe(true)
      await click(button('Back'))
      expect(visible('.details-card')).toBe(true)
    })

    it('has the cart at the thumb, as a sheet with the send button', async () => {
      await open()
      await toSelection()
      expect(document.body.querySelector('.cart-panel')).toBeNull()
      await click(addButtonOf('ThinkPad T14'))
      await click(document.body.querySelector<HTMLElement>('.cart-bar-button')!)
      expect(cartLines()).toEqual(['ThinkPad T14'])
      await click(button('Submit request'))
      expect(api.create).toHaveBeenCalled()
    })
  })

  describe('leaving', () => {
    async function openRouted() {
      const pinia = createPinia()
      setActivePinia(pinia)
      useAuthStore().user = EMPLOYEE
      const router = createRouter({
        history: createMemoryHistory(),
        routes: [
          { path: '/', name: 'dashboard', component: { render: () => null } },
          { path: '/portal/new', name: 'portal-new', component: NewRequestView },
        ],
      })
      await router.push('/portal/new')
      const wrapper = mount(
        defineComponent({
          render: () =>
            h(NMessageProvider, null, {
              default: () => [
                h(ErrorPopover),
                h(NDialogProvider, null, { default: () => h(RouterView) }),
              ],
            }),
        }),
        { attachTo: document.body, global: { plugins: [i18n, pinia, router] } },
      )
      await flushPromises()
      return { wrapper, router }
    }

    it('asks before throwing away a request that was not sent', async () => {
      const { wrapper, router } = await openRouted()
      // Nothing entered yet: nothing to lose.
      await router.push('/')
      expect(router.currentRoute.value.name).toBe('dashboard')

      await router.push('/portal/new')
      await flushPromises()
      await click(addButtonOf('ThinkPad T14'))
      const leaving = router.push('/')
      await flushPromises()
      expect(bodyText()).toContain('Really cancel this request?')
      await click(button('Keep editing'))
      await leaving
      expect(router.currentRoute.value.name).toBe('portal-new')

      const again = router.push('/')
      await flushPromises()
      await click(button('Yes, cancel'))
      await again
      expect(router.currentRoute.value.name).toBe('dashboard')
      wrapper.unmount()
    })

    it("closes the open cart first on back, as with a phone's back gesture", async () => {
      const restore = fakeMatchMedia(375)
      try {
        const { wrapper, router } = await openRouted()
        await toSelection()
        await click(document.body.querySelector<HTMLElement>('.cart-bar-button')!)
        expect(visible('.cart-panel')).toBe(true)
        router.back()
        await flushPromises()
        expect(visible('.cart-panel')).toBe(false)
        expect(router.currentRoute.value.query.step).toBe('catalog')
        // The next back leads to the details, still without asking.
        router.back()
        await flushPromises()
        expect(visible('.details-card')).toBe(true)
        expect(bodyText()).not.toContain('Really cancel this request?')
        wrapper.unmount()
      } finally {
        restore()
      }
    })

    it('cancels from the X with the same question, asked once', async () => {
      const { wrapper, router } = await openRouted()
      await choosePurpose('Workshop')
      await click(button('Cancel request'))
      expect(bodyText()).toContain('Really cancel this request?')
      await click(button('Yes, cancel'))
      await flushPromises()
      // Asked once: a second question on the way out would have kept the page.
      expect(router.currentRoute.value.name).toBe('dashboard')
      wrapper.unmount()
    })
  })

  describe('catalog', () => {
    it('asks for the catalog of the suggested period and opens the first group', async () => {
      await open()
      expect(api.catalog).toHaveBeenCalledWith({ start: TODAY, end: IN_FIVE_DAYS })
      const groups = [...document.body.querySelectorAll('.groups .name')].map((g) => g.textContent)
      // Accessory groups appear inside their parent, not as their own tile.
      expect(groups).toEqual(['Laptops', 'Headsets', 'Ink', 'Software', 'Something else'])
      expect(bodyText()).toContain('Laptop · any model')
      expect(bodyText()).toContain('Accessories')
      expect(bodyText()).toContain('USB-C Dock')
    })

    it('offers "any model" only where the group allows it and there is a choice', async () => {
      await open()
      await toSelection()
      await click(button('Headsets'))
      expect(bodyText()).toContain('Jabra Evolve2')
      expect(bodyText()).not.toContain('any model')
      await click(button('Ink'))
      expect(bodyText()).not.toContain('any model')
    })

    it('collects accessories in one block, compatible ones from other groups included', async () => {
      const t14 = { ...T14, accessories: [INK.id] }
      api.catalog.mockResolvedValue([
        catalogCategory({ id: 'c-laptops', name: 'Laptops', models: [t14, AIR] }),
        catalogCategory({
          id: 'c-docks',
          name: 'Docks',
          parent_id: 'c-laptops',
          holds_accessories: true,
          models: [DOCK],
        }),
        catalogCategory({
          id: 'c-ink',
          name: 'Ink',
          model_choice: 'specific_only',
          holds_accessories: true,
          models: [INK],
        }),
      ])
      await open()
      const block = document.body.querySelector('.accessories')!
      expect(block.textContent).toContain('Accessories')
      const row = (label: string) => addButtonOf(label).closest('.option')!.textContent
      // A group with a single option names it in the hint instead of a heading.
      expect(block.querySelector('.sub-heading')).toBeNull()
      expect(row('USB-C Dock')).toContain('Docks')
      // Compatible with only one of the laptops: the hint says which.
      expect(row('HP 305 ink')).toContain('Fits ThinkPad T14')
      await toSelection()
      await click(button('Ink'))
      expect(row('HP 305 ink')).toContain('Fits ThinkPad T14')
    })

    it('shows unmarked subcategories as groups of their own, not as accessories', async () => {
      api.catalog.mockResolvedValue([
        catalogCategory({ id: 'c-laptops', name: 'Laptops', models: [T14] }),
        catalogCategory({ id: 'c-14', name: '14 inch', parent_id: 'c-laptops', models: [AIR] }),
      ])
      await open()
      expect(document.body.querySelector('.accessories')).toBeNull()
      expect(addButtonOf('MacBook Air').closest('.option')!.textContent).toContain('14 inch')
    })

    it('offers only "any model" where IT picks the model', async () => {
      api.catalog.mockResolvedValue([
        catalogCategory({
          id: 'c-mde',
          name: 'Scanners',
          item_name: 'Scanner',
          model_choice: 'any_only',
          models: [catalogModel({ id: 'm-ht60', full_name: 'Handtec HT60' })],
        }),
      ])
      await open()
      expect(bodyText()).toContain('Scanner · any model')
      expect(bodyText()).not.toContain('Handtec HT60')
      // Searching for the model finds the group instead.
      await typeInto(document.body.querySelector<HTMLInputElement>('.search input')!, 'HT60')
      expect(bodyText()).toContain('Scanner · any model')
      expect(bodyText()).not.toContain('Handtec HT60')
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
      await toSelection()
      await typeInto(field('Search, e.g. headset'), 'beamer')
      expect(bodyText()).toContain('Nothing found for “beamer”.')
      expect(bodyText()).toContain('Item not in the catalog?')
      // The search term is taken over as the description.
      expect(field('Describe the device or item').value).toBe('beamer')
      await click(button('Add'))
      expect(cartLines()).toEqual(['beamer'])
    })

    it('lists what fits the employee’s own devices as a group of its own, opened first', async () => {
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
      await toSelection()
      const fitting = document.body.querySelector('.group.fitting')!
      expect(fitting.textContent).toContain('For your devices')
      // It covers one device and opens first.
      expect(fitting.textContent).toContain('1')
      expect(fitting.classList).toContain('active')
      const content = document.body.querySelector('.browser .main')!.textContent
      expect(content).toContain('PRN-0007')
      expect(content).not.toContain('Toner')

      await click(addButtonOf('HP 305 ink'))
      expect(cartLines()).toEqual(['HP 305 ink'])
    })

    it('does not ask for the quick pick when it is switched off', async () => {
      await mountPage(NewRequestView, {
        url: '/portal/new',
        flags: { consumable_quick_pick: false },
      })
      expect(api.myConsumables).not.toHaveBeenCalled()
      expect(document.body.querySelector('.group.fitting')).toBeNull()
    })
  })

  describe('building and submitting a request', () => {
    it('can only be submitted with something in the cart', async () => {
      await open()
      expect(bodyText()).toContain('What you choose in the next step shows up here.')
      expect(button('Submit request').disabled).toBe(true)
      await click(addButtonOf('ThinkPad T14'))
      expect(button('Submit request').disabled).toBe(false)
    })

    it('leads back to the purpose when it is missing on sending', async () => {
      await open()
      await toSelection()
      await choosePurpose('   ')
      await click(addButtonOf('ThinkPad T14'))
      await click(button('Submit request'))
      expect(api.create).not.toHaveBeenCalled()
      expect(visible('.details-card')).toBe(true)
      expect(document.body.querySelector('.details-card .error')?.textContent).toContain(
        'Please enter a purpose',
      )
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
      await toSelection('Workshop in Munich')
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
        replaces: null,
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
      await toSelection('Back pain')
      await click(button('Something else'))
      await typeInto(field('Describe the device or item'), 'Standing desk')
      await click(button('Add'))
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
              identifier_label: '',
              name: 'Laptops',
              item_name: 'Laptop',
              code: 'NB',
              icon: 'laptop',
              kind: 'hardware',
              device_naming: 'none',
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

    it('replaces an open request with its confirmed lines', async () => {
      const [air, touch] = earlier().items
      api.get.mockResolvedValue({
        ...earlier(),
        status: 'confirmed',
        items: [
          { ...air!, quantity_confirmed: 1 },
          { ...touch!, quantity_confirmed: 0 },
        ],
      })
      await open({ url: '/portal/new?replace=r-old' })
      expect(bodyText()).toContain('Replaces R-2026-0007')
      expect(bodyText()).not.toContain('Prefilled from')
      // Not confirmed at all: the line is left out.
      expect(cartLines()).toEqual(['MacBook Air'])
      await click(button('Submit request'))
      expect(api.create).toHaveBeenCalledWith(
        expect.objectContaining({
          title: 'Trade fair',
          follows: null,
          replaces: 'r-old',
          items: [
            { category: null, asset_model: 'm-air', description: '', quantity: 1, note: 'Silver' },
          ],
        }),
      )
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
        replaces: null,
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
