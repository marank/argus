import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { activityApi } from '@/api/activity'
import type { Schemas } from '@/api/types'
import DateRangeInput from '@/components/table/DateRangeInput.vue'
import ActivityLogView from '@/views/activity/ActivityLogView.vue'

import { button, click } from './dom'
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

  async function show(url?: string) {
    const result = await mountPage(ActivityLogView, {}, { url })
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
        activity({
          id: 'r4',
          area: 'consumables',
          kind: 'consumable_adjustment',
          subject_label: 'USB-C cable · Store',
          quantity: -1,
        }),
      ]),
    )
    await show()
    const [handOut, stock, deleted, corrected] = rows()
    expect(handOut!.textContent).toContain('Handed out · 3 items')
    expect(handOut!.textContent).toContain('Ian Tech')
    expect(handOut!.textContent).toContain('Max Muster')
    expect(handOut!.querySelector('a')?.getAttribute('href')).toBe(`/request/${ID}`)
    // The step says the direction; only a correction shows its sign.
    expect(stock!.textContent).toContain('Stock issued · 2 units')
    expect(corrected!.textContent).toContain('Stock corrected · -1 units')
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

  it('names the device of each allocation and removal', async () => {
    vi.spyOn(activityApi, 'list').mockResolvedValue(
      page([
        activity({ kind: 'request_released', quantity: null, detail: 'NB-0012 · ThinkPad T14' }),
        activity({
          id: 'r2',
          kind: 'request_allocated',
          quantity: null,
          detail: 'NB-0013 · ThinkPad T14 (automatically)',
        }),
      ]),
    )
    await show()
    const [released, allocated] = rows()
    expect(released!.textContent).toContain('Allocation removed · NB-0012 · ThinkPad T14')
    expect(allocated!.textContent).toContain('Allocated · NB-0013 · ThinkPad T14 (automatically)')
  })

  it('shows only the steps of one request when linked from it, until asked for all', async () => {
    const list = vi.spyOn(activityApi, 'list').mockResolvedValue(page([activity()]))
    const { router } = await show(`/?subject=${ID}`)
    expect(list).toHaveBeenCalledWith(expect.objectContaining({ subject: ID }))
    const bar = document.body.querySelector('.subject')!
    expect(bar.textContent).toContain('Only activities of')
    expect(bar.querySelector('a')?.textContent).toBe('REQ-2026-0042 – Workshop')

    await click(button('Show all'))
    expect(list).toHaveBeenLastCalledWith(expect.objectContaining({ subject: null }))
    expect(document.body.querySelector('.subject')).toBeNull()
    expect(router.currentRoute.value.query.subject).toBeUndefined()
  })
})
