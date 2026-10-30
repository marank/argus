import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'

import { ApiError } from '@/api/client'
import { assetsApi } from '@/api/inventory'
import { assetModelsApi, locationsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import AssetFormDrawer from '@/components/inventory/AssetFormDrawer.vue'

import { button, click } from './dom'
import {
  bodyText,
  field,
  locationRef,
  makeAsset,
  makeModel,
  modelRef,
  mountPage,
  page,
  pick,
  stubPickers,
  type,
  userRef,
} from './inventoryHelpers'

async function openDrawer(
  asset: Schemas['AssetDetailOut'] | null = null,
  flags: Record<string, boolean> = {},
) {
  const state = reactive({
    show: false,
    asset,
    'onUpdate:show': (value: boolean) => (state.show = value),
    onSaved: vi.fn<(saved: unknown) => void>(),
  })
  const { wrapper } = await mountPage(AssetFormDrawer, state, { flags })
  state.show = true
  await flushPromises()
  return { wrapper, state }
}

describe('AssetFormDrawer', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    stubPickers()
    vi.mocked(assetModelsApi.list).mockResolvedValue(page([makeModel()]))
    vi.mocked(locationsApi.list).mockResolvedValue(page([locationRef() as never]))
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  async function drawer(...args: Parameters<typeof openDrawer>) {
    const result = await openDrawer(...args)
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('waits for a model before a new device can be saved', async () => {
    const { wrapper } = await drawer()
    expect(bodyText()).toContain('New device')
    expect(button('Save').disabled).toBe(true)
    await pick(wrapper, assetModelsApi.list, 'm1')
    expect(button('Save').disabled).toBe(false)
  })

  it('offers individually tracked models for the device and bulk models as consumables', async () => {
    await drawer()
    const params = vi.mocked(assetModelsApi.list).mock.calls.map(([p]) => p)
    expect(params).toContainEqual(expect.objectContaining({ tracking: 'serialized' }))
    expect(params).toContainEqual(expect.objectContaining({ tracking: 'bulk' }))
  })

  it('hides the consumables field with the consumables module off', async () => {
    await drawer(null, { consumables: false })
    expect(bodyText()).not.toContain('Consumables')
    const params = vi.mocked(assetModelsApi.list).mock.calls.map(([p]) => p)
    expect(params).not.toContainEqual(expect.objectContaining({ tracking: 'bulk' }))
  })

  it('creates a device with what was filled in and stock defaults for the rest', async () => {
    const created = makeAsset({ id: 'a9' })
    const create = vi.spyOn(assetsApi, 'create').mockResolvedValue(created)
    const { wrapper, state } = await drawer()
    await pick(wrapper, assetModelsApi.list, 'm1')
    await pick(wrapper, locationsApi.list, 'l1')
    await type('Serial number', 'CN-123')
    await type('Hostname', 'nb-0099')
    await click('Save')

    expect(create).toHaveBeenCalledWith(
      expect.objectContaining({
        model: 'm1',
        inventory_number: '',
        serial_number: 'CN-123',
        hostname: 'nb-0099',
        location: 'l1',
        status: 'in_stock',
        condition: 'new',
        is_loanable: true,
        assigned_to: null,
        consumables: [],
      }),
    )
    expect(state.onSaved).toHaveBeenCalledWith(created)
    expect(state.show).toBe(false)
  })

  it('edits a device starting from its stored values', async () => {
    const asset = makeAsset({
      assigned_to: userRef(),
      status: 'in_use',
      consumables: [modelRef('Dock WD19', 'bulk', 'm9')],
      notes: 'Keyboard sticks',
    })
    const update = vi.spyOn(assetsApi, 'update').mockResolvedValue(asset)
    await drawer(asset)
    expect(bodyText()).toContain('Edit device · NB-0042')
    expect(field('Serial number').value).toBe('SN-1')
    await type('Notes', 'Keyboard replaced')
    await click('Save')

    expect(update).toHaveBeenCalledWith(
      'a1',
      expect.objectContaining({
        model: 'm1',
        inventory_number: 'NB-0042',
        status: 'in_use',
        condition: 'good',
        location: 'l1',
        assigned_to: 'u1',
        consumables: ['m9'],
        purchase_price: '1299.00',
        notes: 'Keyboard replaced',
      }),
    )
  })

  it('shows what the server rejected at the field and stays open', async () => {
    vi.spyOn(assetsApi, 'create').mockRejectedValue(
      new ApiError(400, 'Check the form.', { serial_number: ['Serial number already exists.'] }),
    )
    const { wrapper, state } = await drawer()
    await pick(wrapper, assetModelsApi.list, 'm1')
    await type('Serial number', 'SN-1')
    await click('Save')

    expect(document.body.querySelector('.ar-form')!.textContent).toContain(
      'Serial number already exists.',
    )
    expect(state.show).toBe(true)
    expect(state.onSaved).not.toHaveBeenCalled()

    // Changing the field takes the complaint away.
    await type('Serial number', 'SN-2')
    expect(document.body.querySelector('.ar-form')!.textContent).not.toContain('already exists')
  })
})
