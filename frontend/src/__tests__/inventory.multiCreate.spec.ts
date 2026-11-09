import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive, type Component } from 'vue'

import { ApiError } from '@/api/client'
import { assetsApi } from '@/api/inventory'
import { assetModelsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import BulkCreateModal from '@/components/inventory/BulkCreateModal.vue'
import SeriesCreateModal from '@/components/inventory/SeriesCreateModal.vue'

import { button, click, fieldErrors } from './dom'
import {
  bodyText,
  field,
  makeModel,
  mountPage,
  page,
  pick,
  stubPickers,
  type,
} from './inventoryHelpers'

const created = (count: number) =>
  Array.from({ length: count }, (_, i) => ({ id: `a${i}` })) as Schemas['AssetOut'][]

/** The series preview waits 250 ms for typing to settle. */
const settle = async () => {
  await vi.advanceTimersByTimeAsync(300)
  await flushPromises()
}

describe('creating many devices', () => {
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

  async function open(component: Component) {
    const state = reactive({
      show: false,
      'onUpdate:show': (value: boolean) => (state.show = value),
      onCreated: vi.fn<() => void>(),
    })
    const { wrapper } = await mountPage(component, state)
    unmount = () => wrapper.unmount()
    state.show = true
    await flushPromises()
    return { wrapper, state }
  }

  describe('SeriesCreateModal', () => {
    const PREVIEW = { first: 'NB-0100', last: 'NB-0109', sequence: 'Notebooks (NB-)' }
    beforeEach(() => {
      vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    })
    afterEach(() => {
      vi.useRealTimers()
    })

    it('asks for a model before it shows any numbers', async () => {
      const preview = vi.spyOn(assetsApi, 'seriesPreview')
      await open(SeriesCreateModal)
      await settle()
      expect(bodyText()).toContain('Pick a model')
      expect(button('Create 10 devices').disabled).toBe(true)
      expect(preview).not.toHaveBeenCalled()
    })

    it('only offers active, numbered serial models', async () => {
      await open(SeriesCreateModal)
      expect(assetModelsApi.list).toHaveBeenCalledWith(
        expect.objectContaining({ tracking: 'serialized', is_active: true, numbered: true }),
      )
    })

    it('previews the inventory numbers the series will take', async () => {
      vi.mocked(assetModelsApi.list).mockResolvedValue(page([makeModel()]))
      const preview = vi.spyOn(assetsApi, 'seriesPreview').mockResolvedValue(PREVIEW)
      const { wrapper } = await open(SeriesCreateModal)
      await pick(wrapper, assetModelsApi.list, 'm1')
      await settle()

      expect(preview).toHaveBeenLastCalledWith('m1', 10)
      expect(bodyText()).toContain('NB-0100')
      expect(bodyText()).toContain('NB-0109')
      expect(bodyText()).toContain('Notebooks (NB-)')
      expect(button('Create 10 devices').disabled).toBe(false)

      preview.mockResolvedValue({ first: 'NB-0100', last: 'NB-0100', sequence: 'Notebooks' })
      await type('Quantity', '1')
      await settle()
      expect(preview).toHaveBeenLastCalledWith('m1', 1)
      expect(button('Create 1 devices').disabled).toBe(false)
    })

    it('says why no numbers can be drawn and does not submit', async () => {
      vi.mocked(assetModelsApi.list).mockResolvedValue(page([makeModel()]))
      vi.spyOn(assetsApi, 'seriesPreview').mockRejectedValue(
        new ApiError(400, 'The model has no number sequence.'),
      )
      const { wrapper } = await open(SeriesCreateModal)
      await pick(wrapper, assetModelsApi.list, 'm1')
      await settle()
      expect(bodyText()).toContain('The model has no number sequence.')
      expect(button('Create 10 devices').disabled).toBe(true)
    })

    it("takes the model's supplier and list price and creates the series", async () => {
      vi.mocked(assetModelsApi.list).mockResolvedValue(
        page([
          makeModel({ default_supplier: { id: 's1', name: 'Nordlicht' }, list_price: '899.00' }),
        ]),
      )
      vi.spyOn(assetsApi, 'seriesPreview').mockResolvedValue({
        first: 'NB-0100',
        last: 'NB-0102',
        sequence: 'Notebooks',
      })
      const create = vi.spyOn(assetsApi, 'createSeries').mockResolvedValue(created(3))
      const { wrapper, state } = await open(SeriesCreateModal)
      await pick(wrapper, assetModelsApi.list, 'm1')
      await type('Quantity', '3')
      await settle()
      await click('Create 3 devices')

      expect(create).toHaveBeenCalledWith({
        model: 'm1',
        count: 3,
        condition: 'new',
        is_loanable: true,
        location: null,
        supplier: 's1',
        purchase_date: null,
        purchase_price: '899.00',
        warranty_until: null,
        notes: '',
      })
      expect(bodyText()).toContain('3 devices created (NB-0100 – NB-0102)')
      expect(state.onCreated).toHaveBeenCalledOnce()
      expect(state.show).toBe(false)
    })

    it('shows rejected fields and keeps the modal open', async () => {
      vi.mocked(assetModelsApi.list).mockResolvedValue(page([makeModel()]))
      vi.spyOn(assetsApi, 'seriesPreview').mockResolvedValue(PREVIEW)
      vi.spyOn(assetsApi, 'createSeries').mockRejectedValue(
        new ApiError(400, 'Check the form.', { count: ['Only 4 numbers are left.'] }),
      )
      const { wrapper, state } = await open(SeriesCreateModal)
      await pick(wrapper, assetModelsApi.list, 'm1')
      await settle()
      await click('Create 10 devices')
      expect(fieldErrors().join(' ')).toContain('Only 4 numbers are left.')
      expect(state.show).toBe(true)
    })
  })

  describe('BulkCreateModal', () => {
    it('counts scanned serial numbers whether separated by lines, commas or tabs', async () => {
      await open(BulkCreateModal)
      await type('Serial numbers', 'SN1\nSN2, SN3\tSN4;\n\n  \n')
      expect(bodyText()).toContain('4 serial numbers')
      expect(button('Create (4)')).toBeTruthy()
    })

    it('needs a model and at least one serial number', async () => {
      vi.mocked(assetModelsApi.list).mockResolvedValue(page([makeModel()]))
      const { wrapper } = await open(BulkCreateModal)
      expect(button('Create (0)').disabled).toBe(true)
      await type('Serial numbers', 'SN1')
      expect(button('Create (1)').disabled).toBe(true)
      await pick(wrapper, assetModelsApi.list, 'm1')
      expect(button('Create (1)').disabled).toBe(false)
    })

    it('creates one device per serial number', async () => {
      vi.mocked(assetModelsApi.list).mockResolvedValue(page([makeModel()]))
      const bulk = vi.spyOn(assetsApi, 'bulkCreate').mockResolvedValue(created(2))
      const { wrapper, state } = await open(BulkCreateModal)
      await pick(wrapper, assetModelsApi.list, 'm1')
      await type('Serial numbers', ' SN1 \nSN2\n')
      await click('Create (2)')

      expect(bulk).toHaveBeenCalledWith({
        model: 'm1',
        location: null,
        supplier: null,
        condition: 'new',
        serial_numbers: ['SN1', 'SN2'],
        is_loanable: true,
        notes: '',
      })
      expect(bodyText()).toContain('2 devices created')
      expect(state.onCreated).toHaveBeenCalledOnce()
      expect(state.show).toBe(false)
    })

    it('keeps the scanned numbers when creating fails', async () => {
      vi.mocked(assetModelsApi.list).mockResolvedValue(page([makeModel()]))
      vi.spyOn(assetsApi, 'bulkCreate').mockRejectedValue(
        new ApiError(400, 'Serial number SN1 exists already.'),
      )
      const { wrapper, state } = await open(BulkCreateModal)
      await pick(wrapper, assetModelsApi.list, 'm1')
      await type('Serial numbers', 'SN1\nSN2')
      await click('Create (2)')
      expect(bodyText()).toContain('Serial number SN1 exists already.')
      expect(field('Serial numbers').value).toBe('SN1\nSN2')
      expect(state.show).toBe(true)
    })
  })
})
