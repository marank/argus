import { flushPromises } from '@vue/test-utils'
import { NSelect } from 'naive-ui'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { assetsApi, eventsApi } from '@/api/inventory'
import { assetModelsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import DateRangeInput from '@/components/table/DateRangeInput.vue'
import AssetListView from '@/views/inventory/AssetListView.vue'
import EventLogView from '@/views/inventory/EventLogView.vue'

import { click, hasButton } from './dom'
import {
  addFilter,
  bodyText,
  groupBy,
  makeAsset,
  makeModel,
  modelRef,
  mountPage,
  page,
  pick,
  stubPickers,
  userRef,
} from './inventoryHelpers'

describe('inventory lists', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    stubPickers()
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    localStorage.clear()
    vi.restoreAllMocks()
  })

  async function show(
    component: Parameters<typeof mountPage>[0],
    options: Parameters<typeof mountPage>[2] = {},
  ) {
    const result = await mountPage(component, {}, options)
    unmount = () => result.wrapper.unmount()
    return result
  }

  const rows = () =>
    [...document.body.querySelectorAll<HTMLElement>('tbody tr')].filter(
      (tr) => !tr.querySelector('.n-data-table-empty'),
    )

  describe('AssetListView', () => {
    const asset = (id: string, number: string) =>
      ({ ...makeAsset({ id, inventory_number: number }) }) as unknown as Schemas['AssetOut']

    it('lists devices grouped by category', async () => {
      vi.mocked(assetsApi.list).mockResolvedValue(page([asset('a1', 'NB-0001')]))
      await show(AssetListView, { permissions: { assets: 'write' } })
      expect(assetsApi.list).toHaveBeenCalledWith(
        expect.objectContaining({
          ordering: 'model__category__sort_order,model__category__name,inventory_number',
        }),
      )
      expect(bodyText()).toContain('Laptops')
      expect(bodyText()).toContain('NB-0001')
    })

    it('sorts by inventory number alone without grouping', async () => {
      await show(AssetListView, { permissions: { assets: 'write' } })
      await groupBy('No grouping')
      expect(assetsApi.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ ordering: 'inventory_number' }),
      )
    })

    it('takes the status filter from the link', async () => {
      await show(AssetListView, { url: '/assets?status=in_repair' })
      expect(assetsApi.list).toHaveBeenCalledWith(
        expect.objectContaining({ status: ['in_repair'] }),
      )
    })

    it('filters by model', async () => {
      vi.mocked(assetModelsApi.list).mockResolvedValue(page([makeModel()]))
      const { wrapper } = await show(AssetListView)
      await addFilter(wrapper, 'Model')
      expect(assetModelsApi.list).toHaveBeenCalledWith(
        expect.objectContaining({ tracking: 'serialized' }),
      )
      await pick(wrapper, assetModelsApi.list, 'm1')
      expect(assetsApi.list).toHaveBeenLastCalledWith(
        expect.objectContaining({ model: 'm1', page: 1 }),
      )
    })

    it('names who a reserved device is set aside for', async () => {
      const reserved = {
        ...asset('a3', 'NB-0003'),
        status: 'reserved',
        reserved_for: {
          id: 'r1',
          number: 'RES-2026-00023',
          requester: userRef('Erika Muster', 'u9'),
          status: 'confirmed',
        },
      } as Schemas['AssetOut']
      vi.mocked(assetsApi.list).mockResolvedValue(page([reserved]))
      await show(AssetListView)
      const row = rows().find((tr) => tr.textContent?.includes('NB-0003'))!
      expect(row.textContent).toContain('reserved for Erika Muster')
      expect(row.textContent).toContain('RES-2026-00023')
    })

    it('opens a device from its row', async () => {
      vi.mocked(assetsApi.list).mockResolvedValue(page([asset('a7', 'NB-0007')]))
      const { router } = await show(AssetListView)
      rows()
        .find((tr) => tr.textContent?.includes('NB-0007'))!
        .click()
      await flushPromises()
      expect(router.currentRoute.value.fullPath).toBe('/asset/a7')
    })

    it('goes to a new device once it is saved', async () => {
      vi.mocked(assetModelsApi.list).mockResolvedValue(page([makeModel()]))
      vi.spyOn(assetsApi, 'create').mockResolvedValue(makeAsset({ id: 'a9' }))
      const { wrapper, router } = await show(AssetListView, { permissions: { assets: 'write' } })
      await click('New device')
      // The drawer's model picker comes after the toolbar's.
      await pick(wrapper, assetModelsApi.list, 'm1', -2)
      await click('Save')
      expect(router.currentRoute.value.fullPath).toBe('/asset/a9')
    })

    it('offers creating devices only with the right to change them', async () => {
      await show(AssetListView, { permissions: { assets: 'read' } })
      for (const action of ['New device', 'Scan in multiple', 'Create series'])
        expect(hasButton(action)).toBe(false)
    })
  })

  describe('EventLogView', () => {
    function logged(
      overrides: Partial<Schemas['AssetEventWithAssetOut']> = {},
    ): Schemas['AssetEventWithAssetOut'] {
      return {
        id: 'e1',
        kind: 'component_replaced',
        occurred_at: '2026-10-01T09:00:00Z',
        description: '',
        component: 'Battery 54 Wh',
        component_serial: '',
        component_type: null,
        previous_serial: '',
        cost: '89.50',
        asset_request: null,
        performed_by: userRef('Ian Tech', 'u9'),
        related_user: null,
        asset: { id: 'a1', inventory_number: 'NB-0042', model: modelRef() },
        ...overrides,
      } as Schemas['AssetEventWithAssetOut']
    }

    it('shows service work by default, not hand-outs', async () => {
      const list = vi.spyOn(eventsApi, 'list').mockResolvedValue(page([]))
      await show(EventLogView)
      expect(list).toHaveBeenCalledWith(
        expect.objectContaining({
          kind: ['component_replaced', 'repair', 'maintenance', 'inspection'],
        }),
      )
    })

    it('shows each entry with its device, component, cost and technician', async () => {
      vi.spyOn(eventsApi, 'list').mockResolvedValue(
        page([
          logged(),
          logged({
            id: 'e2',
            kind: 'assigned',
            component: '',
            cost: null,
            related_user: userRef('Max Muster', 'u2'),
          }),
        ]),
      )
      await show(EventLogView)
      const [service, handOut] = rows().map((tr) => tr.textContent ?? '')
      expect(service).toContain('NB-0042')
      expect(service).toContain('Component replaced')
      expect(service).toContain('Battery 54 Wh')
      expect(service).toContain('89.50')
      expect(service).toContain('Ian Tech')
      // Without a description, the employee involved stands in.
      expect(handOut).toContain('Handed out')
      expect(handOut).toContain('Max Muster')
    })

    it('narrows the log to a period', async () => {
      const list = vi.spyOn(eventsApi, 'list').mockResolvedValue(page([]))
      const { wrapper } = await show(EventLogView)
      await addFilter(wrapper, 'Date')
      const range = wrapper.findComponent(DateRangeInput).find('input')
      await range.setValue('1.9.26..30.9.26')
      await range.trigger('blur')
      await flushPromises()
      expect(list).toHaveBeenLastCalledWith(
        expect.objectContaining({ since: '2026-09-01', until: '2026-09-30', page: 1 }),
      )
    })

    it('shows every kind once the kind filter is cleared', async () => {
      const list = vi.spyOn(eventsApi, 'list').mockResolvedValue(page([]))
      const { wrapper } = await show(EventLogView)
      const kinds = wrapper
        .findAllComponents(NSelect)
        .find((s) => s.props('multiple') && !s.props('remote'))!
      kinds.vm.$emit('update:value', [])
      await flushPromises()
      expect(list).toHaveBeenLastCalledWith(expect.objectContaining({ kind: [] }))
    })
  })
})
