import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { activityApi } from '@/api/activity'
import type { Schemas } from '@/api/types'
import DateRangeInput from '@/components/table/DateRangeInput.vue'
import ActivityLogView from '@/views/activity/ActivityLogView.vue'

import { addFilter, mountPage, page, stubPickers, userRef } from './inventoryHelpers'

const ID = '0192f0c4-6a3e-7b4d-9a1e-000000000001'

function activity(overrides: Partial<Schemas['ActivityOut']> = {}): Schemas['ActivityOut'] {
  return {
    id: 'r1',
    occurred_at: '2026-11-18T09:00:00Z',
    area: 'requests',
    kind: 'request_handed_out',
    subject_id: ID,
    subject_label: 'REQ-2026-0042 – Workshop',
    actor: userRef('Ian Tech', 'u9'),
    related_user: userRef('Max Muster', 'u2'),
    quantity: 3,
    detail: '',
    ...overrides,
  }
}

describe('activity log', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => stubPickers())
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    localStorage.clear()
    vi.restoreAllMocks()
  })

  async function show() {
    const result = await mountPage(ActivityLogView, {}, {})
    unmount = () => result.wrapper.unmount()
    return result
  }
  const rows = () =>
    [...document.body.querySelectorAll<HTMLElement>('tbody tr')].filter(
      (tr) => !tr.querySelector('.n-data-table-empty'),
    )

  it('shows one row per step with its object, people and size', async () => {
    vi.spyOn(activityApi, 'list').mockResolvedValue(
      page([
        activity(),
        activity({
          id: 'r2',
          area: 'consumables',
          kind: 'consumable_issue',
          subject_label: 'USB-C cable · Store',
          quantity: -2,
          related_user: null,
        }),
        activity({
          id: 'r3',
          area: 'assets',
          kind: 'asset_deleted',
          subject_id: null,
          subject_label: 'NB-0042 · Dell Latitude',
          quantity: null,
        }),
      ]),
    )
    await show()
    const [handOut, stock, deleted] = rows()
    expect(handOut!.textContent).toContain('Handed out · 3 items')
    expect(handOut!.textContent).toContain('Ian Tech')
    expect(handOut!.textContent).toContain('Max Muster')
    expect(handOut!.querySelector('a')?.getAttribute('href')).toBe(`/request/${ID}`)
    expect(stock!.textContent).toContain('Stock issued · -2 units')
    expect(stock!.querySelector('a')?.getAttribute('href')).toBe('/consumables')
    // A deleted object has no page to open.
    expect(deleted!.textContent).toContain('NB-0042')
    expect(deleted!.querySelector('a')).toBeNull()
  })

  it('narrows the log to a period', async () => {
    const list = vi.spyOn(activityApi, 'list').mockResolvedValue(page([]))
    const { wrapper } = await show()
    expect(list).toHaveBeenCalledWith(expect.objectContaining({ ordering: '-occurred_at' }))
    await addFilter(wrapper, 'Time')
    const range = wrapper.findComponent(DateRangeInput).find('input')
    await range.setValue('1.11.26..18.11.26')
    await range.trigger('blur')
    await flushPromises()
    expect(list).toHaveBeenLastCalledWith(
      expect.objectContaining({ since: '2026-11-01', until: '2026-11-18', page: 1 }),
    )
  })
})
