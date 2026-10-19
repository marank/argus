import { describe, expect, it } from 'vitest'

import {
  formatParts,
  parseFormat,
  readParts,
  segmentAt,
  step,
  typeDigit,
} from '@/utils/dateSegments'

const FORMAT = 'dd.MM.yyyy HH:mm'
const parts = { day: 31, month: 1, year: 2026, hour: 9, minute: 5 }

describe('date segments', () => {
  it('finds segments in a format', () => {
    expect(parseFormat('dd.MM.yyyy').map((s) => [s.kind, s.start, s.end])).toEqual([
      ['day', 0, 2],
      ['month', 3, 5],
      ['year', 6, 10],
    ])
    expect(segmentAt(parseFormat('dd.MM.yyyy'), 4)).toBe(1)
  })

  it('round-trips text', () => {
    const text = formatParts(FORMAT, parts)
    expect(text).toBe('31.01.2026 09:05')
    expect(readParts(text, FORMAT)).toEqual(parts)
    expect(readParts('31.01.20', FORMAT)).toBeNull()
  })

  it('steps with wrap-around and keeps the day valid', () => {
    expect(step(parts, 'month', 1)).toMatchObject({ month: 2, day: 28 }) // 31 Jan → Feb
    expect(step(parts, 'minute', -10)).toMatchObject({ minute: 55 })
    expect(step({ ...parts, day: 1 }, 'day', -1)).toMatchObject({ day: 31 })
  })

  it('overwrites a segment while typing', () => {
    let result = typeDigit(parts, 'day', '', '1')
    expect(result).toMatchObject({ complete: false, buffer: '1' })
    result = typeDigit(result.parts, 'day', result.buffer, '5')
    expect(result).toMatchObject({ complete: true, parts: { day: 15 } })

    // A digit that cannot start a two-digit day completes immediately.
    expect(typeDigit(parts, 'day', '', '4')).toMatchObject({ complete: true, parts: { day: 4 } })
    expect(typeDigit(parts, 'month', '', '3')).toMatchObject({
      complete: true,
      parts: { month: 3 },
    })
  })

  it('collects four digits for the year', () => {
    let result = typeDigit(parts, 'year', '', '2')
    for (const digit of '027') result = typeDigit(result.parts, 'year', result.buffer, digit)
    expect(result).toMatchObject({ complete: true, parts: { year: 2027 } })
  })
})
