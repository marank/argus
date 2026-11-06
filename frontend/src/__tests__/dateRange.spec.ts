import { describe, expect, it } from 'vitest'

import { formatDateRange, parseDateRange } from '@/utils/dateRange'

const TODAY = new Date(2026, 10, 6)
const parse = (text: string) => parseDateRange(text, TODAY)
/** The text as the field shows it once read. */
const normal = (text: string) => {
  const range = parse(text)
  return range ? formatDateRange(range) : range
}

describe('date ranges', () => {
  it('reads two days in any of the usual forms', () => {
    for (const text of [
      '0611..2311',
      '06.11..23.11',
      '6.11..23.11.',
      '06.11.26..23.11.26',
      '06.11.2026..23.11.2026',
      '061126..231126',
      '06112026..23112026',
      ' 6-11 .. 23/11 ',
    ])
      expect({ text, range: parse(text) }).toEqual({
        text,
        range: { from: '2026-11-06', until: '2026-11-23' },
      })
    expect(normal('0611..2311')).toBe('06.11.26..23.11.26')
  })

  it('leaves an end open', () => {
    expect(parse('0611..')).toEqual({ from: '2026-11-06', until: null })
    expect(parse('..2311')).toEqual({ from: null, until: '2026-11-23' })
    expect(normal('0611..')).toBe('06.11.26..')
    expect(normal('..23.11.2026')).toBe('..23.11.26')
  })

  it('takes a single day as that day alone', () => {
    expect(parse('0611')).toEqual({ from: '2026-11-06', until: '2026-11-06' })
    expect(normal('6.11.26')).toBe('06.11.26')
    // A day alone is in the current month.
    expect(parse('24')).toEqual({ from: '2026-11-24', until: '2026-11-24' })
  })

  it('knows today', () => {
    expect(normal('t..')).toBe('06.11.26..')
    expect(normal('..heute')).toBe('..06.11.26')
  })

  it('treats an empty text as no filter', () => {
    expect(parse('  ')).toBeNull()
    expect(formatDateRange({ from: null, until: null })).toBe('')
  })

  it('refuses what is not a day or a range', () => {
    for (const text of ['..', '3102', '0613', '12345', 'abc', '06.11..x', '2311..0611', '1.2.3.4'])
      expect({ text, range: parse(text) }).toEqual({ text, range: undefined })
  })
})
