import { describe, expect, it } from 'vitest'

import { fromIsoDate, toIsoDate } from '@/composables/useFormat'
import { toneOf } from '@/utils/status'

describe('date helpers', () => {
  it('round-trips ISO dates in local time', () => {
    const ts = fromIsoDate('2026-03-31')
    expect(toIsoDate(ts)).toBe('2026-03-31')
  })

  it('handles empty values', () => {
    expect(toIsoDate(null)).toBeNull()
    expect(fromIsoDate('')).toBeNull()
  })
})

describe('status tones', () => {
  it('maps known statuses and falls back to default', () => {
    expect(toneOf('requestStatus', 'ready')).toBe('success')
    expect(toneOf('assetStatus', 'unknown')).toBe('default')
  })
})
