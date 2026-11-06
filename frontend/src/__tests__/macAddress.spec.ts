import { describe, expect, it } from 'vitest'

import { formatMacAddress } from '@/utils/macAddress'

describe('formatMacAddress', () => {
  it('writes every spelling as pairs with colons', () => {
    for (const typed of [
      'aa:bb:cc:dd:ee:0f',
      'AA-BB-CC-DD-EE-0F',
      'aabbccddee0f',
      'aabb.ccdd.ee0f',
    ])
      expect({ typed, mac: formatMacAddress(typed) }).toEqual({ typed, mac: 'AA:BB:CC:DD:EE:0F' })
  })

  it('leaves what is no MAC address as typed', () => {
    expect(formatMacAddress(' AA-BB ')).toBe('AA-BB')
    expect(formatMacAddress('')).toBe('')
  })
})
