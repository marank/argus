/**
 * Date ranges typed as text, as in the filter panel: two days with ".." between them,
 * each written loosely. "0611..2311", "6.11..23.11" and "06.11.2026..23.11.26" all mean
 * the 6th to the 23rd of November; "0611.." is open towards the end, "..2311" towards the
 * start, and a single day ("0611") is that day alone. Missing months and years are the
 * current ones; "t" / "h" (today / heute) is today.
 *
 * Every range is shown in one form: DD.MM.YY, with ".." between the two ends.
 */

/** Ends of a range as ISO dates; null for an open end. */
export interface DateRange {
  from: string | null
  until: string | null
}

const TODAY_WORDS = new Set(['t', 'today', 'h', 'heute'])

const pad = (n: number) => String(n).padStart(2, '0')
const iso = (y: number, m: number, d: number) => `${y}-${pad(m)}-${pad(d)}`

/** One day, or null if it is not a valid one. */
// eslint-disable-next-line complexity -- one branch per accepted way of writing a day
function parseDay(text: string, today: Date): string | null {
  const value = text.trim().toLowerCase()
  if (TODAY_WORDS.has(value)) return iso(today.getFullYear(), today.getMonth() + 1, today.getDate())

  let parts: string[]
  if (/^\d+$/.test(value)) {
    // Digits only: DD, DDMM, DDMMYY or DDMMYYYY.
    const lengths: Record<number, number[]> = {
      1: [1],
      2: [2],
      4: [2, 2],
      6: [2, 2, 2],
      8: [2, 2, 4],
    }
    const sizes = lengths[value.length]
    if (!sizes) return null
    let at = 0
    parts = sizes.map((size) => value.slice(at, (at += size)))
  } else {
    parts = value.split(/[.\-/\s]+/).filter(Boolean)
    if (!parts.length || parts.length > 3 || parts.some((p) => !/^\d+$/.test(p))) return null
  }

  const [day, month, year] = parts.map(Number) as [number, number?, number?]
  const m = month ?? today.getMonth() + 1
  let y = year ?? today.getFullYear()
  if (parts[2] !== undefined && parts[2].length <= 2) y += 2000
  else if (parts[2] !== undefined && parts[2].length !== 4) return null

  const date = new Date(y, m - 1, day)
  if (date.getFullYear() !== y || date.getMonth() !== m - 1 || date.getDate() !== day) return null
  return iso(y, m, day)
}

/**
 * The range a text names: null for an empty text (no filter), undefined if it cannot be
 * read (or ends before it starts).
 */
// eslint-disable-next-line complexity -- one branch per accepted way of writing a range
export function parseDateRange(text: string, today = new Date()): DateRange | null | undefined {
  const value = text.trim()
  if (!value) return null
  const at = value.indexOf('..')
  if (at < 0) {
    const day = parseDay(value, today)
    return day ? { from: day, until: day } : undefined
  }
  const [start, end] = [value.slice(0, at).trim(), value.slice(at + 2).trim()]
  if (!start && !end) return undefined
  const from = start ? parseDay(start, today) : null
  const until = end ? parseDay(end, today) : null
  if ((start && !from) || (end && !until)) return undefined
  if (from && until && from > until) return undefined
  return { from, until }
}

/** A day as DD.MM.YY. */
function formatDay(isoDate: string): string {
  const [y, m, d] = isoDate.split('-')
  return `${d}.${m}.${y!.slice(2)}`
}

/** The text form of a range: "06.11.26..23.11.26", "06.11.26..", "..23.11.26" or "06.11.26". */
export function formatDateRange(range: DateRange): string {
  const { from, until } = range
  if (from && until && from === until) return formatDay(from)
  if (!from && !until) return ''
  return `${from ? formatDay(from) : ''}..${until ? formatDay(until) : ''}`
}
