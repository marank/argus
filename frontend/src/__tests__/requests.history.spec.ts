import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { Schemas } from '@/api/types'
import RequestHistory from '@/components/requests/detail/RequestHistory.vue'
import { i18n } from '@/i18n'

import { JANE, event, makeRequest } from './requestsHelpers'

type Event = Schemas['AssetRequestEventOut']

const NO_SCHEDULE = {
  items: [],
  added: [],
  removed: [],
  handover_mode: null,
  pickup_at: null,
  pickup_location: null,
  notified: null,
}

/** The history's entries as shown, newest first: title (with actor) and detail lines. */
function history(...events: Event[]) {
  const wrapper = mount(RequestHistory, {
    props: { assetRequest: makeRequest({ events }) },
    global: { plugins: [i18n] },
  })
  return wrapper.findAll('.n-timeline-item').map((item) => ({
    title: item.find('.n-timeline-item-content__title').text().replace(/\s+/g, ' '),
    lines: item.findAll('.detail').map((line) => line.text()),
  }))
}

describe('RequestHistory', () => {
  it('lists the newest step first, with who did it', () => {
    const entries = history(
      event('created', { requester: null, follows: null }, { actor: JANE }),
      event('confirmed', { comment: '' }, { at: '2026-10-03T10:00:00Z' }),
    )
    expect(entries.map((e) => e.title)).toEqual([
      'Confirmed by IT · Max IT',
      'Requested · Jane Doe',
    ])
  })

  it('names the employee a request was recorded for and the request it follows', () => {
    const [entry] = history(event('direct', { requester: 'Jane Doe', follows: 'R-2026-0007' }))
    expect(entry!.title).toBe('Direct hand-out recorded · Max IT')
    expect(entry!.lines).toEqual(['for Jane Doe', 'Follows R-2026-0007'])
  })

  it('shows the reason given with a decision', () => {
    const [entry] = history(event('rejected', { comment: 'No budget this year.' }))
    expect(entry!.title).toContain('Rejected by IT')
    expect(entry!.lines).toEqual(['No budget this year.'])
  })

  it('says when an assignment was removed', () => {
    const [entry] = history(event('assigned', { team: null, assignee: null }))
    expect(entry!.lines).toEqual(['Nobody'])
    const [named] = history(event('assigned', { team: 'Service desk', assignee: 'Max IT' }))
    expect(named!.lines).toEqual(['Service desk · Max IT'])
  })

  it('reads allocations by one person within a minute as one step', () => {
    const entries = history(
      event('allocated', { items: ['INV-001'] }, { at: '2026-10-02T10:00:00Z' }),
      event('allocated', { items: ['INV-002'] }, { at: '2026-10-02T10:00:40Z' }),
      // Someone else, or later: a separate step.
      event('allocated', { items: ['INV-003'] }, { at: '2026-10-02T10:00:50Z', actor: JANE }),
      event('allocated', { items: ['INV-004'] }, { at: '2026-10-02T10:05:00Z', actor: JANE }),
    )
    expect(entries).toEqual([
      { title: '1 item allocated · Jane Doe', lines: ['INV-004'] },
      { title: '1 item allocated · Jane Doe', lines: ['INV-003'] },
      { title: '2 items allocated · Max IT', lines: ['INV-001, INV-002'] },
    ])
  })

  it('counts removed allocations', () => {
    const [entry] = history(event('released', { items: ['INV-001', 'INV-002'] }))
    expect(entry!.title).toBe('2 allocations removed · Max IT')
  })

  it('shows the planned handover when marked ready, and if the employee was not told', () => {
    const [entry] = history(
      event('ready', {
        ...NO_SCHEDULE,
        items: ['INV-001'],
        handover_mode: 'pickup',
        pickup_location: 'HQ / IT desk',
        notified: false,
      }),
    )
    expect(entry!.title).toBe('Marked ready for pickup · Max IT')
    expect(entry!.lines).toEqual([
      'Pickup with signature · HQ / IT desk · Employee not notified',
      'INV-001',
    ])
  })

  it('lists only what changed when marked ready again', () => {
    const [entry] = history(
      event('ready', {
        ...NO_SCHEDULE,
        handover_mode: 'delivery',
        added: ['INV-005'],
        removed: ['INV-001', 'INV-002'],
      }),
    )
    expect(entry!.lines).toEqual(['Delivered by IT', 'Added: INV-005', 'Removed: INV-001, INV-002'])
  })

  it('shows how the devices were handed out and to whom', () => {
    const [entry] = history(
      event('handed_out', {
        items: ['INV-001'],
        method: 'delivered',
        received_by: 'Jane Doe',
        location: 'Office 2.14',
        missing: [],
      }),
    )
    expect(entry!.title).toBe('Handed out · Max IT')
    expect(entry!.lines).toEqual([
      'Delivered by IT · Received by: Jane Doe · Office 2.14',
      'INV-001',
    ])
  })

  it('names the lines handed out and taken back without a device', () => {
    const [returned, handed] = history(
      event('handed_out', {
        items: [],
        method: 'direct',
        received_by: null,
        location: null,
        missing: ['2× Laptops'],
      }),
      event('returned', { items: [], damaged: [], notes: null, missing: ['1× Laptops'] }),
    )
    expect(handed!.lines).toContain('Without a device: 2× Laptops')
    expect(returned!.lines).toEqual(['Without a device: 1× Laptops'])
  })

  it('shows what came back damaged and the notes of a return', () => {
    const [entry] = history(
      event('returned', {
        items: ['INV-001', 'INV-002'],
        damaged: ['INV-002'],
        notes: 'Display cracked.',
        missing: [],
      }),
    )
    expect(entry!.title).toBe('Taken back · Max IT')
    expect(entry!.lines).toEqual(['INV-001, INV-002', 'Damaged: INV-002', 'Display cracked.'])
  })

  it('leaves out the damage line when everything came back fine', () => {
    const [entry] = history(
      event('returned', { items: ['INV-001'], damaged: [], notes: null, missing: [] }),
    )
    expect(entry!.lines).toEqual(['INV-001'])
  })

  it('shows the old and the new return date of an extension', () => {
    const [entry] = history(event('extended', { previous: '2026-11-06', end_date: '2026-11-20' }))
    expect(entry!.title).toBe('Loan extended · Max IT')
    expect(entry!.lines).toEqual(['11/06/2026 → 11/20/2026'])
  })

  it('shows steps without details, also without an actor', () => {
    const [entry] = history(event('completed', {}, { actor: null }))
    expect(entry).toEqual({ title: 'Completed', lines: [] })
  })
})
