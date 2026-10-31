import { describe, expect, it } from 'vitest'

import {
  allocationCode,
  allocationModel,
  anyModelLabel,
  isPast,
  isReturnable,
  itemLabel,
} from '@/utils/requests'
import { toneOf } from '@/utils/status'

type Item = Parameters<typeof itemLabel>[0]
type AllocationLike = Parameters<typeof isReturnable>[0]

const laptops = { id: 'c1', name: 'Laptops', item_name: 'Laptop' }
const item = (fields: Record<string, unknown>) =>
  ({ label: 'Label', category: null, asset_model: null, description: '', ...fields }) as Item
const allocation = (fields: Record<string, unknown>) =>
  ({ asset: null, consumable: null, license: null, quantity: 1, ...fields }) as AllocationLike
const model = (full_name: string) => ({ model: { full_name } })

describe('request item labels', () => {
  it('names the singular item for "any model"', () => {
    expect(anyModelLabel(laptops)).toBe('Laptop · any model')
  })

  it('falls back to the category name without a singular', () => {
    expect(anyModelLabel({ name: 'Headsets', item_name: '' })).toBe('Headsets · any model')
    expect(anyModelLabel({ name: 'Headsets' })).toBe('Headsets · any model')
  })

  it('says "any model" for plain category requests', () => {
    expect(itemLabel(item({ category: laptops }))).toBe('Laptop · any model')
  })

  it('keeps the label of model lines and free text', () => {
    expect(itemLabel(item({ category: laptops, asset_model: { id: 'm1' } }))).toBe('Label')
    expect(itemLabel(item({ category: laptops, description: '64 GB RAM' }))).toBe('Label')
    expect(itemLabel(item({}))).toBe('Label')
  })
})

describe('allocations', () => {
  it('names the model of a device, consumable or license seat', () => {
    expect(allocationModel(allocation({ asset: model('Dell XPS') }))).toBe('Dell XPS')
    expect(allocationModel(allocation({ consumable: model('USB-C cable') }))).toBe('USB-C cable')
    expect(allocationModel(allocation({ license: model('Office 365') }))).toBe('Office 365')
    expect(allocationModel(allocation({}))).toBe('')
  })

  it('codes a device by inventory number', () => {
    expect(allocationCode(allocation({ asset: { inventory_number: 'IT-0042' } }))).toBe('IT-0042')
  })

  it('codes a license seat by the device it is on, if any', () => {
    const onDevice = { device: { inventory_number: 'IT-0007' } }
    expect(allocationCode(allocation({ license: onDevice }))).toBe('IT-0007')
    expect(allocationCode(allocation({ license: { device: null } }))).toBe('')
  })

  it('codes consumables by quantity', () => {
    expect(allocationCode(allocation({ consumable: model('Cable'), quantity: 3 }))).toBe('3×')
  })

  it('expects devices and seats back, not consumables', () => {
    expect(isReturnable(allocation({ asset: model('Dell XPS') }))).toBe(true)
    expect(isReturnable(allocation({ license: model('Office') }))).toBe(true)
    expect(isReturnable(allocation({ consumable: model('Cable') }))).toBe(false)
  })
})

describe('status tones', () => {
  it.each([
    ['assetStatus', 'lost', 'error'],
    ['requestStatus', 'ready', 'success'],
    ['orderStatus', 'draft', 'warning'],
    ['condition', 'defective', 'error'],
    ['issueStatus', 'resolved', 'success'],
    ['approval', 'pending', 'warning'],
    ['ldapSync', 'skipped', 'warning'],
  ])('gives %s %s the tone %s', (group, value, tone) => {
    expect(toneOf(group, value)).toBe(tone)
  })

  it('falls back to default for an unknown group or status', () => {
    expect(toneOf('nothing', 'open')).toBe('default')
    expect(toneOf('assetStatus', 'unknown')).toBe('default')
  })
})

describe('isPast', () => {
  const now = new Date('2026-10-30T15:00:00')

  it('compares a moment with now, a plain day with today', () => {
    expect(isPast('2026-10-30T14:00:00', now)).toBe(true)
    expect(isPast('2026-10-30T16:00:00', now)).toBe(false)
    expect(isPast('2026-10-29', now)).toBe(true)
    // Today is not over yet.
    expect(isPast('2026-10-30', now)).toBe(false)
  })

  it('treats a missing date as not passed', () => {
    expect(isPast(null, now)).toBe(false)
    expect(isPast(undefined, now)).toBe(false)
  })
})
