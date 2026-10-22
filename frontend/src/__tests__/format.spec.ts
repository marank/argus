import { describe, expect, it } from 'vitest'

import { fromIsoDate, toIsoDate } from '@/composables/useFormat'
import { modelLabel } from '@/utils/models'
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

describe('model label', () => {
  const cradle = { name: '4-slot cradle', full_name: 'Scanova 4-slot cradle' }

  it('adds the designation that tells same-named models apart', () => {
    expect(modelLabel({ ...cradle, designation: 'CRD-SX5X-4SC' })).toBe(
      'Scanova 4-slot cradle (CRD-SX5X-4SC)',
    )
  })

  it('leaves out a designation that only repeats the name', () => {
    expect(modelLabel({ ...cradle, designation: '4-slot cradle' })).toBe('Scanova 4-slot cradle')
    expect(modelLabel(cradle)).toBe('Scanova 4-slot cradle')
  })
})
