import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Schemas } from '@/api/types'
import HandoverProtocolView from '@/views/requests/HandoverProtocolView.vue'

import { click } from './dom'
import {
  IT_MAX,
  REQUEST_ID,
  device,
  lentRequest,
  makeItem,
  mountWithApp,
  user,
} from './requestsHelpers'

type AssetRequest = Schemas['AssetRequestOut']

const api = vi.hoisted(() => ({ get: vi.fn<(id: string) => Promise<unknown>>() }))

vi.mock('@/api/requests', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/requests')>()),
  requestsApi: { get: api.get },
}))

/** Label → value of the facts at the top of the sheet (and of each return). */
const facts = (root: ParentNode = document.body) =>
  Object.fromEntries(
    [...root.querySelectorAll('.facts > div')].map((f) => [
      f.querySelector('dt')!.textContent.trim(),
      f.querySelector('dd')!.textContent.replace(/\s+/g, ' ').trim(),
    ]),
  )

const tableRows = (root: ParentNode) =>
  [...root.querySelectorAll('tbody tr')].map((r) =>
    [...r.querySelectorAll('td')].map((c) => c.textContent.replace(/\s+/g, ' ').trim()),
  )

describe('HandoverProtocolView', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    api.get.mockReset()
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  async function protocol(request: AssetRequest) {
    api.get.mockResolvedValue(request)
    const result = await mountWithApp(HandoverProtocolView, { id: REQUEST_ID })
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('records who received what, when and how', async () => {
    const request = lentRequest()
    request.items[0]!.allocations[1]!.handout_note = 'Charger missing'
    await protocol(request)

    expect(api.get).toHaveBeenCalledWith(REQUEST_ID)
    const sheet = document.body.querySelector('.sheet')!
    expect(sheet.textContent).toContain('R-2026-0042')
    expect(facts(sheet)).toMatchObject({
      'Requested by': 'Jane Doe',
      Department: 'Sales',
      Purpose: 'Training in Munich',
      Period: '11/02/2026 → 11/06/2026',
      Handover: 'Handed out by IT',
      'Received by': 'Jane Doe',
      'Handed out by': 'Max IT',
    })
    expect(tableRows(sheet)).toEqual([
      ['INV-001', 'Acme Laptop 14', 'SN-INV-001', '1', ''],
      ['INV-002', 'Acme Laptop 14', 'SN-INV-002', '1', 'Charger missing'],
    ])
    expect(sheet.querySelector('.signature')!.textContent).toContain('Signature · Jane Doe')
  })

  it('names who recorded a hand-out done by a colleague, and where it was delivered', async () => {
    const request = lentRequest()
    request.handover = {
      ...request.handover!,
      method: 'delivered',
      location: 'Office 2.14',
      recorded_by: user('Terminal', 'terminal'),
    }
    await protocol(request)
    expect(facts()).toMatchObject({
      Handover: 'Delivered by IT',
      'Recorded via': 'Terminal',
      'Delivered to': 'Office 2.14',
    })
  })

  it('leaves out "recorded via" when the same person handed out and recorded', async () => {
    await protocol(lentRequest())
    expect(Object.keys(facts())).not.toContain('Recorded via')
  })

  it('says permanent for a request without return date', async () => {
    await protocol(lentRequest({ duration: 'permanent', end_date: null }))
    expect(facts()['Period']).toBe('11/02/2026 → permanent')
  })

  it('adds each return with what came back damaged', async () => {
    const request = lentRequest({
      returns: [
        {
          id: 'ret-1',
          returned_at: '2026-11-06T15:00:00Z',
          returned_by: IT_MAX,
          notes: 'All in the bag.',
        },
      ],
    })
    request.items = [
      makeItem({
        quantity_requested: 2,
        quantity_confirmed: 2,
        allocations: [
          device('INV-001', 'Laptop 14', {
            device_return: 'ret-1',
            returned_damaged: true,
            return_note: 'Cracked display',
          }),
          // Still with the employee: not part of this return.
          device('INV-002', 'Laptop 14'),
        ],
      }),
    ]
    await protocol(request)

    const sections = document.body.querySelectorAll('section.return')
    expect(sections).toHaveLength(1)
    expect(facts(sections[0])).toMatchObject({ 'Taken back by': 'Max IT' })
    expect(sections[0]!.textContent).toContain('All in the bag.')
    expect(tableRows(sections[0]!)).toEqual([
      ['INV-001', 'Acme Laptop 14', 'SN-INV-001', 'Damaged Cracked display'],
    ])
  })

  it('prints the sheet', async () => {
    const print = vi.spyOn(window, 'print').mockImplementation(() => {})
    await protocol(lentRequest())
    await click('Print')
    expect(print).toHaveBeenCalledOnce()
  })
})
