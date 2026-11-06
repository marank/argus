import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { usersApi } from '@/api/accounts'
import { assetsApi, eventsApi } from '@/api/inventory'
import type { Schemas } from '@/api/types'
import AssetDetailView from '@/views/inventory/AssetDetailView.vue'

import { click, hasButton } from './dom'
import {
  bodyText,
  makeAsset,
  modelRef,
  mountPage,
  page,
  pick,
  stubPickers,
  titled,
  userRef,
} from './inventoryHelpers'

const WRITE = { assets: 'write', requests: 'write' } as const

function event(overrides: Partial<Schemas['AssetEventOut']> = {}): Schemas['AssetEventOut'] {
  return {
    id: 'e1',
    kind: 'repair',
    occurred_at: '2026-10-01T09:00:00Z',
    description: 'Display replaced',
    component: 'Display',
    component_serial: '',
    component_type: null,
    previous_serial: '',
    cost: null,
    asset_request: null,
    performed_by: userRef('Ian Tech', 'u9'),
    related_user: null,
    ...overrides,
  }
}

describe('AssetDetailView', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    stubPickers()
    vi.spyOn(assetsApi, 'events').mockResolvedValue([])
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  async function show(
    asset: Schemas['AssetDetailOut'] = makeAsset(),
    permissions: Record<string, 'read' | 'write'> = WRITE,
    flags: Record<string, boolean> = {},
  ) {
    vi.spyOn(assetsApi, 'get').mockResolvedValue(asset)
    const result = await mountPage(AssetDetailView, { id: asset.id }, { permissions, flags })
    unmount = () => result.wrapper.unmount()
    return result
  }

  const history = () => document.body.querySelector('.history')!

  it('shows the device with its history', async () => {
    vi.mocked(assetsApi.events).mockResolvedValue([
      event(),
      event({ id: 'e2', kind: 'created', description: '', component: '', performed_by: null }),
    ])
    await show()
    expect(assetsApi.get).toHaveBeenCalledWith('a1')
    expect(bodyText()).toContain('Dell Latitude 5450')
    expect(bodyText()).toContain('NB-0042')
    expect(bodyText()).toContain('In stock')
    expect(history().textContent).toContain('Repair')
    expect(history().textContent).toContain('Display replaced')
    expect(history().textContent).toContain('By Ian Tech')
    expect(history().textContent).toContain('Created')
  })

  it('offers a request or a quick assignment for a device in stock', async () => {
    const { router } = await show()
    expect(hasButton('Quick assignment')).toBe(true)
    expect(hasButton('Take back')).toBe(false)
    await click('Create request')
    expect(router.currentRoute.value.name).toBe('portal-new')
    expect(router.currentRoute.value.query).toEqual({ asset: 'a1' })
  })

  it('takes back a device that is handed out', async () => {
    const assigned = makeAsset({ status: 'in_use', assigned_to: userRef() })
    const assign = vi.spyOn(assetsApi, 'assign').mockResolvedValue(makeAsset())
    await show(assigned)
    expect(hasButton('Quick assignment')).toBe(false)
    expect(hasButton('Create request')).toBe(false)
    await click('Take back')
    expect(assign).toHaveBeenCalledWith('a1', null)
    // The page shows the state after taking it back.
    expect(assetsApi.get).toHaveBeenCalledTimes(2)
  })

  it('does not offer to hand out a device that is not in stock', async () => {
    await show(makeAsset({ status: 'in_repair' }))
    expect(hasButton('Quick assignment')).toBe(false)
    expect(hasButton('Take back')).toBe(false)
    expect(hasButton('Record service')).toBe(true)
  })

  it('records the quick assignment as a hand-out with the right to do so', async () => {
    await show()
    await click('Quick assignment')
    // The hand-out form asks for a return date.
    expect(bodyText()).toContain('without a request or approval')
    expect(bodyText()).toContain('Return by')
  })

  it('only assigns the device without the right to record hand-outs', async () => {
    vi.mocked(usersApi.list).mockResolvedValue(page([userRef('Max Muster', 'u2') as never]))
    const assign = vi.spyOn(assetsApi, 'assign').mockResolvedValue(makeAsset())
    const { wrapper } = await show(makeAsset(), { assets: 'write' })
    await click('Quick assignment')
    expect(bodyText()).not.toContain('Return by')
    await pick(wrapper, usersApi.list, 'u2')
    await click('Assign')
    expect(assign).toHaveBeenCalledWith('a1', 'u2')
  })

  it('is for viewing only without the right to change devices', async () => {
    await show(makeAsset(), { assets: 'read' })
    for (const action of ['Edit', 'Record service', 'Quick assignment', 'Create request'])
      expect(hasButton(action)).toBe(false)
    expect(titled('Delete')).toEqual([])
  })

  it('deletes the device after confirming and returns to the list', async () => {
    const remove = vi.spyOn(assetsApi, 'remove').mockResolvedValue(true)
    const { router } = await show()
    await click(titled('Delete')[0]!)
    expect(bodyText()).toContain('Delete this record permanently?')
    await click('Confirm')
    expect(remove).toHaveBeenCalledWith('a1')
    expect(router.currentRoute.value.name).toBe('assets')
  })

  it('keeps the device when deleting is cancelled', async () => {
    const remove = vi.spyOn(assetsApi, 'remove')
    const { router } = await show()
    await click(titled('Delete')[0]!)
    await click('Cancel')
    expect(remove).not.toHaveBeenCalled()
    expect(router.currentRoute.value.path).toBe('/')
  })

  it('lets only hand-recorded history entries be deleted', async () => {
    vi.mocked(assetsApi.events).mockResolvedValue([
      event({ id: 'e1', kind: 'repair' }),
      event({ id: 'e2', kind: 'assigned', related_user: userRef() }),
    ])
    const remove = vi.spyOn(eventsApi, 'remove').mockResolvedValue(true)
    await show()
    const deletes = titled('Delete', history())
    expect(deletes).toHaveLength(1)
    await click(deletes[0]!)
    await click('Confirm')
    expect(remove).toHaveBeenCalledWith('e1')
    expect(assetsApi.events).toHaveBeenCalledTimes(2)
  })

  it('gives viewers without write rights no delete on history entries', async () => {
    vi.mocked(assetsApi.events).mockResolvedValue([event()])
    await show(makeAsset(), { assets: 'read' })
    expect(titled('Delete', history())).toEqual([])
  })

  it('lists its own consumables first, then those that fit its model', async () => {
    const dock = modelRef('Dock WD19', 'bulk', 'm8')
    const bag = modelRef('Bag 15"', 'bulk', 'm9')
    await show(makeAsset({ consumables: [dock], model_consumables: [dock, bag] }))
    const items = [...document.body.querySelectorAll('.consumable')].map((el) =>
      el.textContent?.trim(),
    )
    expect(items).toEqual(['Dell Dock WD19', 'Dell Bag 15" via model'])
  })

  it('points to open problem reports of the device', async () => {
    await show(
      makeAsset({
        open_issues: [
          { id: 'i1', kind: 'defect', description: 'Fan is loud' } as Schemas['OwnIssueOut'],
        ],
      }),
    )
    expect(bodyText()).toContain('1 open report')
    expect(bodyText()).toContain('Not working – Fan is loud')
  })

  it('names the request a reserved device is waiting for', async () => {
    await show(
      makeAsset({
        status: 'reserved',
        asset_request: {
          id: 'r1',
          number: 'REQ-0007',
          requester: userRef('Max Muster', 'u2'),
        } as Schemas['ActiveAssetRequestOut'],
      }),
    )
    expect(bodyText()).toContain('Reserved for REQ-0007 (Max Muster)')
  })

  it('reloads after a service was recorded', async () => {
    vi.spyOn(assetsApi, 'addEvent').mockResolvedValue(event())
    await show()
    await click('Record service')
    await click('Save')
    await flushPromises()
    expect(assetsApi.get).toHaveBeenCalledTimes(2)
  })
})
