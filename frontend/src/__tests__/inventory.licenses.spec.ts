import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'

import { usersApi } from '@/api/accounts'
import { ApiError } from '@/api/client'
import { assetsApi, licensesApi } from '@/api/inventory'
import { assetModelsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import DateRangeInput from '@/components/table/DateRangeInput.vue'
import LicenseFormDrawer from '@/components/inventory/LicenseFormDrawer.vue'
import LicenseDetailView from '@/views/inventory/LicenseDetailView.vue'
import LicenseListView from '@/views/inventory/LicenseListView.vue'

import { button, click, hasButton, fieldErrors } from './dom'
import {
  bodyText,
  categoryRef,
  addFilter,
  choose,
  field,
  makeAsset,
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

const OFFICE = modelRef('Microsoft 365 E3', 'license', 'm3')

function makeLicense(overrides: Partial<Schemas['LicenseDetailOut']> = {}) {
  return {
    id: 'l1',
    model: OFFICE,
    category: { ...categoryRef('Office'), kind: 'software' },
    manufacturer: { id: 'mf2', name: 'Microsoft' },
    reference: 'EA-2026',
    license_key: 'XXXX-YYYY',
    seats: 5,
    seats_used: 0,
    assign_to: 'user',
    assignments: [],
    is_expired: false,
    valid_from: '2026-01-01',
    valid_until: '2026-12-31',
    supplier: null,
    purchase_date: null,
    purchase_price: null,
    notes: '',
    created_at: '2026-01-01T09:00:00Z',
    updated_at: '2026-01-01T09:00:00Z',
    ...overrides,
  } satisfies Schemas['LicenseDetailOut']
}

function seat(
  overrides: Partial<Schemas['LicenseAssignmentOut']> = {},
): Schemas['LicenseAssignmentOut'] {
  return {
    id: 'as1',
    user: userRef(),
    asset: null,
    assigned_by: null,
    note: '',
    created_at: '2026-02-01T09:00:00Z',
    ...overrides,
  }
}

const WRITE = { licenses: 'write' } as const

describe('licenses', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date('2026-10-30T10:00:00'))
    stubPickers()
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  describe('LicenseDetailView', () => {
    async function show(
      license: Schemas['LicenseDetailOut'],
      permissions: Record<string, 'read' | 'write'> = WRITE,
    ) {
      vi.spyOn(licensesApi, 'get').mockResolvedValue(license)
      const result = await mountPage(LicenseDetailView, { id: license.id }, { permissions })
      unmount = () => result.wrapper.unmount()
      return result
    }

    it('shows how many seats are used', async () => {
      await show(
        makeLicense({ seats: 5, seats_used: 2, assignments: [seat(), seat({ id: 'as2' })] }),
      )
      expect(bodyText()).toContain('2 / 5 used')
      expect(bodyText()).toContain('Employees')
    })

    it('assigns a seat to an employee when seats go to employees', async () => {
      vi.mocked(usersApi.list).mockResolvedValue(page([userRef('Max Muster', 'u2') as never]))
      const assigned = makeLicense({
        seats_used: 1,
        assignments: [seat({ user: userRef('Max Muster', 'u2'), note: 'Pool' })],
      })
      const assign = vi.spyOn(licensesApi, 'assign').mockResolvedValue(assigned)
      const { wrapper } = await show(makeLicense())
      expect(usersApi.list).toHaveBeenCalledWith(expect.objectContaining({ is_active: true }))
      expect(assetsApi.list).not.toHaveBeenCalled()
      expect(button('Add').disabled).toBe(true)

      await pick(wrapper, usersApi.list, 'u2')
      await type(
        document.body.querySelector<HTMLInputElement>('input[placeholder="Note"]')!,
        'Pool',
      )
      await click('Add')

      expect(assign).toHaveBeenCalledWith('l1', { user: 'u2', note: 'Pool' })
      expect(bodyText()).toContain('Max Muster')
      expect(bodyText()).toContain('1 / 5 used')
    })

    it('assigns a seat to a device when seats go to devices', async () => {
      vi.mocked(assetsApi.list).mockResolvedValue(page([makeAsset() as never]))
      const assign = vi
        .spyOn(licensesApi, 'assign')
        .mockResolvedValue(
          makeLicense({ assign_to: 'device', seats_used: 1, assignments: [seat({ user: null })] }),
        )
      const { wrapper } = await show(makeLicense({ assign_to: 'device' }))
      expect(usersApi.list).not.toHaveBeenCalled()
      await pick(wrapper, assetsApi.list, 'a1')
      await click('Add')
      expect(assign).toHaveBeenCalledWith('l1', { asset: 'a1', note: '' })
    })

    it('names the device and who has it for device seats', async () => {
      await show(
        makeLicense({
          assign_to: 'device',
          seats_used: 1,
          assignments: [
            seat({
              user: null,
              asset: {
                id: 'a1',
                inventory_number: 'NB-0042',
                model: modelRef(),
                assigned_to: userRef(),
              },
            }),
          ],
        }),
      )
      const entry = document.body.querySelector('.assignments li')!.textContent
      expect(entry).toContain('NB-0042')
      expect(entry).toContain('Dell Latitude 5450')
      expect(entry).toContain('Jane Doe')
    })

    it('stops assigning once all seats are used', async () => {
      await show(makeLicense({ seats: 1, seats_used: 1, assignments: [seat()] }))
      expect(bodyText()).toContain('All seats are in use.')
      expect(hasButton('Add')).toBe(false)
    })

    it('does not assign seats of an expired license', async () => {
      await show(makeLicense({ is_expired: true, valid_until: '2026-01-31' }))
      expect(bodyText()).toContain('expired')
      expect(hasButton('Add')).toBe(false)
    })

    it('removes an assignment after confirming', async () => {
      const unassign = vi
        .spyOn(licensesApi, 'unassign')
        .mockResolvedValue(makeLicense({ seats_used: 0 }))
      await show(makeLicense({ seats_used: 1, assignments: [seat()] }))
      await click(titled('Remove assignment')[0]!)
      expect(bodyText()).toContain('Remove the assignment of Jane Doe?')
      await click('Confirm')
      expect(unassign).toHaveBeenCalledWith('l1', 'as1')
      expect(bodyText()).toContain('Not assigned yet.')
    })

    it('deletes the license after confirming and returns to the list', async () => {
      const remove = vi.spyOn(licensesApi, 'remove').mockResolvedValue(true)
      const { router } = await show(makeLicense())
      await click(titled('Delete')[0]!)
      expect(bodyText()).toContain('Dell Microsoft 365 E3: Delete this record permanently?')
      await click('Confirm')
      expect(remove).toHaveBeenCalledWith('l1')
      expect(router.currentRoute.value.name).toBe('licenses')
    })

    it('hides edit and delete without the right to change licenses', async () => {
      await show(makeLicense(), { licenses: 'read' })
      expect(hasButton('Edit')).toBe(false)
      expect(titled('Delete')).toEqual([])
    })

    it('lets read-only viewers neither assign nor remove seats', async () => {
      await show(makeLicense({ seats_used: 1, assignments: [seat()] }), { licenses: 'read' })
      expect(hasButton('Add')).toBe(false)
      expect(titled('Remove assignment')).toEqual([])
    })
  })

  describe('LicenseFormDrawer', () => {
    async function openDrawer(license: Schemas['LicenseDetailOut'] | null = null) {
      vi.mocked(assetModelsApi.list).mockResolvedValue(
        page([makeModel({ ...OFFICE, category: categoryRef('Office') })]),
      )
      const state = reactive({
        show: false,
        license,
        'onUpdate:show': (value: boolean) => (state.show = value),
        onSaved: vi.fn<(saved: unknown) => void>(),
      })
      const { wrapper } = await mountPage(LicenseFormDrawer, state)
      unmount = () => wrapper.unmount()
      state.show = true
      await flushPromises()
      return { wrapper, state }
    }

    it('only offers software and waits for one to be picked', async () => {
      const { wrapper } = await openDrawer()
      expect(assetModelsApi.list).toHaveBeenCalledWith(
        expect.objectContaining({ tracking: 'license', is_active: true }),
      )
      expect(button('Save').disabled).toBe(true)
      await pick(wrapper, assetModelsApi.list, 'm3')
      expect(button('Save').disabled).toBe(false)
    })

    it('creates a license whose seats go to devices', async () => {
      const create = vi.spyOn(licensesApi, 'create').mockResolvedValue(makeLicense())
      const { wrapper, state } = await openDrawer()
      await pick(wrapper, assetModelsApi.list, 'm3')
      await type('Seats', '25')
      await choose('Devices')
      await type('License key', 'ABCD-EFGH')
      await click('Save')

      expect(create).toHaveBeenCalledWith({
        model: 'm3',
        reference: '',
        license_key: 'ABCD-EFGH',
        seats: 25,
        assign_to: 'device',
        valid_from: null,
        valid_until: null,
        supplier: null,
        purchase_date: null,
        purchase_price: null,
        notes: '',
      })
      expect(state.onSaved).toHaveBeenCalledOnce()
      expect(state.show).toBe(false)
    })

    it('keeps whom seats go to once seats are assigned', async () => {
      await openDrawer(makeLicense({ seats_used: 2 }))
      const radios = [...document.body.querySelectorAll<HTMLInputElement>('.n-radio-input')]
      expect(radios.length).toBe(2)
      expect(radios.every((r) => r.disabled)).toBe(true)
    })

    it('lets whom seats go to change while none are assigned', async () => {
      const update = vi.spyOn(licensesApi, 'update').mockResolvedValue(makeLicense())
      await openDrawer(makeLicense())
      expect(field('Contract / reference').value).toBe('EA-2026')
      await choose('Devices')
      await click('Save')
      expect(update).toHaveBeenCalledWith(
        'l1',
        expect.objectContaining({
          model: 'm3',
          assign_to: 'device',
          seats: 5,
          valid_until: '2026-12-31',
        }),
      )
    })

    it('shows the fields the server rejected', async () => {
      vi.spyOn(licensesApi, 'update').mockRejectedValue(
        new ApiError(400, 'Check the form.', { seats: ['Fewer seats than assigned.'] }),
      )
      const { state } = await openDrawer(makeLicense())
      await click('Save')
      expect(fieldErrors().join(' ')).toContain('Fewer seats than assigned.')
      expect(state.show).toBe(true)
    })
  })

  describe('LicenseListView', () => {
    const row = (overrides: Partial<Schemas['LicenseOut']>) =>
      ({ ...makeLicense(), ...overrides }) as unknown as Schemas['LicenseOut']

    async function list(url = '/') {
      const result = await mountPage(LicenseListView, {}, { permissions: WRITE, url })
      unmount = () => result.wrapper.unmount()
      return result
    }

    it('lines up seat numbers of different lengths', async () => {
      vi.spyOn(licensesApi, 'list').mockResolvedValue(
        page([
          row({ id: 'l1', seats: 100, seats_used: 5 }),
          row({ id: 'l2', seats: 10, seats_used: 3 }),
        ]),
      )
      await list()
      const counts = [...document.body.querySelectorAll('.seats .count')].map(
        (el) => el.textContent,
      )
      expect(counts).toEqual(['  5 / 100 used', '  3 /  10 used'])
    })

    it('marks expired licenses and those ending within the warning period', async () => {
      vi.spyOn(licensesApi, 'list').mockResolvedValue(
        page([
          row({ id: 'l1', valid_until: '2026-09-30', is_expired: true }),
          row({ id: 'l2', valid_until: '2026-11-15' }),
          row({ id: 'l3', valid_until: '2027-06-30' }),
          row({ id: 'l4', valid_until: null }),
        ]),
      )
      await list()
      const cells = [...document.body.querySelectorAll('tbody tr')]
        .filter((tr) => tr.querySelector('.seats'))
        .map((tr) => tr.textContent ?? '')
      expect(cells[0]).toContain('expired')
      expect(cells[1]).toContain('expires soon')
      expect(cells[2]).not.toMatch(/expire/)
      expect(cells[3]).toContain('perpetual')
    })

    it('filters to licenses ending within the warning period', async () => {
      const fetch = vi.spyOn(licensesApi, 'list').mockResolvedValue(page([]))
      const { wrapper } = await list()
      expect(fetch).toHaveBeenLastCalledWith(expect.objectContaining({ expires_until: null }))
      await addFilter(wrapper, 'Valid until')
      const range = wrapper.findComponent(DateRangeInput).find('input')
      await range.setValue('..29.12.26')
      await range.trigger('blur')
      await flushPromises()
      expect(fetch).toHaveBeenLastCalledWith(
        expect.objectContaining({ expires_from: null, expires_until: '2026-12-29' }),
      )
    })

    it('starts filtered when coming from the dashboard', async () => {
      const fetch = vi.spyOn(licensesApi, 'list').mockResolvedValue(page([]))
      await list('/licenses?expiring=1')
      expect(fetch).toHaveBeenCalledWith(expect.objectContaining({ expires_until: '2026-12-29' }))
    })

    it('opens a license from its row', async () => {
      vi.spyOn(licensesApi, 'list').mockResolvedValue(page([row({ id: 'l7' })]))
      const { router } = await list()
      const tr = [...document.body.querySelectorAll<HTMLElement>('tbody tr')].find((el) =>
        el.querySelector('.seats'),
      )!
      tr.click()
      await flushPromises()
      expect(router.currentRoute.value.fullPath).toBe('/license/l7')
    })
  })
})
