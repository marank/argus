import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive, type Component } from 'vue'

import { usersApi } from '@/api/accounts'
import { assetsApi, consumablesApi } from '@/api/inventory'
import { requestsApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import AssetEventModal from '@/components/inventory/AssetEventModal.vue'
import QuickAssignModal from '@/components/inventory/QuickAssignModal.vue'
import { useFeaturesStore } from '@/stores/features'

import { button, click } from './dom'
import {
  bodyText,
  choose,
  hasField,
  locationRef,
  modelRef,
  mountPage,
  optionsBeside,
  page,
  pick,
  selectOption,
  stubPickers,
  toggle,
  type,
  userRef,
} from './inventoryHelpers'

const NOW = new Date('2026-10-30T10:00:00')

describe('modals on the device page', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(NOW)
    stubPickers()
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  async function open(
    component: Component,
    options: { flags?: Record<string, boolean>; loanDays?: number } = {},
  ) {
    const state = reactive({
      show: false,
      assetId: 'a1',
      'onUpdate:show': (value: boolean) => (state.show = value),
      onSaved: vi.fn<(saved: unknown) => void>(),
    })
    const { wrapper } = await mountPage(component, state, { flags: options.flags })
    unmount = () => wrapper.unmount()
    if (options.loanDays !== undefined)
      useFeaturesStore().settings!.rules.default_loan_days = options.loanDays
    state.show = true
    await flushPromises()
    return { wrapper, state }
  }

  describe('QuickAssignModal', () => {
    const assigned = { id: 'r1' } as Schemas['AssetRequestOut']

    beforeEach(() => {
      vi.mocked(usersApi.list).mockResolvedValue(page([userRef('Max Muster', 'u2') as never]))
    })

    it('only lists active employees, not terminals', async () => {
      await open(QuickAssignModal)
      expect(usersApi.list).toHaveBeenCalledWith(
        expect.objectContaining({ is_active: true, is_terminal: false }),
      )
    })

    it('needs an employee before assigning', async () => {
      const { wrapper } = await open(QuickAssignModal)
      expect(button('Assign').disabled).toBe(true)
      await pick(wrapper, usersApi.list, 'u2')
      expect(button('Assign').disabled).toBe(false)
    })

    it('lends the device until the end of the default loan period', async () => {
      const quickAssign = vi.spyOn(requestsApi, 'quickAssign').mockResolvedValue(assigned)
      const { wrapper, state } = await open(QuickAssignModal)
      await pick(wrapper, usersApi.list, 'u2')
      await click('Assign')

      // Five days including today.
      expect(quickAssign).toHaveBeenCalledWith({
        asset: 'a1',
        requester: 'u2',
        duration: 'temporary',
        start_date: null,
        end_date: '2026-11-03',
      })
      expect(bodyText()).toContain('Device assigned.')
      expect(state.onSaved).toHaveBeenCalledWith(assigned)
      expect(state.show).toBe(false)
    })

    it("follows the site's loan period", async () => {
      const quickAssign = vi.spyOn(requestsApi, 'quickAssign').mockResolvedValue(assigned)
      const { wrapper } = await open(QuickAssignModal, { loanDays: 14 })
      await pick(wrapper, usersApi.list, 'u2')
      await click('Assign')
      expect(quickAssign).toHaveBeenCalledWith(expect.objectContaining({ end_date: '2026-11-12' }))
    })

    it('hands out permanently without a return date', async () => {
      const quickAssign = vi.spyOn(requestsApi, 'quickAssign').mockResolvedValue(assigned)
      const { wrapper } = await open(QuickAssignModal)
      expect(hasField('Return by')).toBe(true)
      await choose('Permanent')
      expect(hasField('Return by')).toBe(false)
      await pick(wrapper, usersApi.list, 'u2')
      await click('Assign')
      expect(quickAssign).toHaveBeenCalledWith(
        expect.objectContaining({ duration: 'permanent', end_date: null }),
      )
    })

    it('starts empty again after being closed', async () => {
      const { wrapper, state } = await open(QuickAssignModal)
      await pick(wrapper, usersApi.list, 'u2')
      await choose('Permanent')
      state.show = false
      await flushPromises()
      state.show = true
      await flushPromises()
      expect(button('Assign').disabled).toBe(true)
      expect(hasField('Return by')).toBe(true)
    })
  })

  describe('AssetEventModal', () => {
    it('offers only the kinds a technician records by hand', async () => {
      const { wrapper } = await open(AssetEventModal)
      expect(optionsBeside(wrapper, 'Repair')).toEqual([
        'Battery replaced',
        'Component replaced',
        'Repair',
        'Maintenance',
        'Inspection',
        'Note',
      ])
    })

    it('asks for the component only for replacements and repairs', async () => {
      const { wrapper } = await open(AssetEventModal)
      expect(hasField('Component')).toBe(true)
      await selectOption(wrapper, 'Inspection')
      expect(hasField('Component')).toBe(false)
      await selectOption(wrapper, 'Repair')
      expect(hasField('Component')).toBe(true)
    })

    it('records the service with its time, component and cost', async () => {
      const addEvent = vi
        .spyOn(assetsApi, 'addEvent')
        .mockResolvedValue({ id: 'e1' } as Schemas['AssetEventOut'])
      const { state } = await open(AssetEventModal)
      await type('Component', 'Battery 54 Wh')
      await type('Component serial', 'BAT-77')
      await type('Cost', '89.5')
      await type('Description', 'Swollen battery')
      await click('Save')

      expect(addEvent).toHaveBeenCalledWith('a1', {
        kind: 'battery_replaced',
        occurred_at: NOW.toISOString(),
        description: 'Swollen battery',
        component: 'Battery 54 Wh',
        component_serial: 'BAT-77',
        cost: '89.50',
        consume: null,
      })
      expect(state.onSaved).toHaveBeenCalledOnce()
      expect(state.show).toBe(false)
    })

    it('books the consumable used for the service', async () => {
      vi.mocked(consumablesApi.list).mockResolvedValue(
        page([
          {
            id: 's1',
            model: modelRef('Battery 54 Wh', 'bulk', 'm5'),
            location: locationRef(),
            available_quantity: 4,
          } as Schemas['ConsumableOut'],
        ]),
      )
      const addEvent = vi
        .spyOn(assetsApi, 'addEvent')
        .mockResolvedValue({ id: 'e1' } as Schemas['AssetEventOut'])
      const { wrapper } = await open(AssetEventModal)
      expect(hasField('Consumable')).toBe(false)
      await toggle('Use consumable')
      await pick(wrapper, consumablesApi.list, 's1')
      await type('Qty', '2')
      await click('Save')

      expect(addEvent).toHaveBeenCalledWith(
        'a1',
        expect.objectContaining({ consume: { consumable_id: 's1', quantity: 2 } }),
      )
    })

    it('does not offer consumables with the module off', async () => {
      await open(AssetEventModal, { flags: { consumables: false } })
      expect(bodyText()).not.toContain('Use consumable')
    })
  })
})
