/**
 * Segment model for fixed-width date strings such as `dd.MM.yyyy HH:mm`.
 *
 * Pure functions (no DOM) so the typing behaviour of DateField can be unit tested:
 * typing overwrites the focused segment, arrow keys step it, and the day is kept
 * valid for the month.
 */

export type SegmentKind = 'day' | 'month' | 'year' | 'hour' | 'minute'

export interface Segment {
  kind: SegmentKind
  start: number
  end: number
}

const TOKENS: Record<string, SegmentKind> = {
  dd: 'day',
  MM: 'month',
  yyyy: 'year',
  HH: 'hour',
  mm: 'minute',
}

const LIMITS: Record<SegmentKind, [number, number]> = {
  day: [1, 31],
  month: [1, 12],
  year: [1, 9999],
  hour: [0, 23],
  minute: [0, 59],
}

export function parseFormat(format: string): Segment[] {
  const segments: Segment[] = []
  for (const match of format.matchAll(/yyyy|MM|dd|HH|mm/g)) {
    segments.push({
      kind: TOKENS[match[0]]!,
      start: match.index,
      end: match.index + match[0].length,
    })
  }
  return segments
}

export function segmentAt(segments: Segment[], position: number): number {
  const index = segments.findIndex((s) => position >= s.start && position <= s.end)
  if (index >= 0) return index
  // Between segments (on a separator): take the following one.
  const next = segments.findIndex((s) => position < s.start)
  return next >= 0 ? next : segments.length - 1
}

const pad = (value: number, width: number) => String(value).padStart(width, '0')

export function formatParts(format: string, parts: Record<SegmentKind, number>): string {
  return format
    .replace('yyyy', pad(parts.year, 4))
    .replace('MM', pad(parts.month, 2))
    .replace('dd', pad(parts.day, 2))
    .replace('HH', pad(parts.hour, 2))
    .replace('mm', pad(parts.minute, 2))
}

export function partsFromDate(date: Date): Record<SegmentKind, number> {
  return {
    day: date.getDate(),
    month: date.getMonth() + 1,
    year: date.getFullYear(),
    hour: date.getHours(),
    minute: date.getMinutes(),
  }
}

/** Read the segment values from text; null when it does not match the format. */
export function readParts(text: string, format: string): Record<SegmentKind, number> | null {
  if (text.length !== format.length) return null
  const parts = partsFromDate(new Date())
  for (const segment of parseFormat(format)) {
    const raw = text.slice(segment.start, segment.end)
    if (!/^\d+$/.test(raw)) return null
    parts[segment.kind] = Number(raw)
  }
  return parts
}

const daysInMonth = (year: number, month: number) => new Date(year, month, 0).getDate()

/** Clamp every segment into its range and the day into the month's length. */
export function normalize(parts: Record<SegmentKind, number>): Record<SegmentKind, number> {
  const result = { ...parts }
  for (const kind of Object.keys(LIMITS) as SegmentKind[]) {
    const [min, max] = LIMITS[kind]
    result[kind] = Math.min(Math.max(result[kind], min), max)
  }
  result.day = Math.min(result.day, daysInMonth(result.year, result.month))
  return result
}

/** Step a segment up or down, wrapping within its range (years do not wrap). */
export function step(
  parts: Record<SegmentKind, number>,
  kind: SegmentKind,
  delta: number,
): Record<SegmentKind, number> {
  const result = { ...parts }
  if (kind === 'year') {
    result.year = Math.max(1, result.year + delta)
  } else {
    const [min, max] = kind === 'day' ? [1, daysInMonth(parts.year, parts.month)] : LIMITS[kind]
    const span = max - min + 1
    result[kind] = ((((result[kind] - min + delta) % span) + span) % span) + min
  }
  return normalize(result)
}

export interface TypeResult {
  parts: Record<SegmentKind, number>
  /** Digits typed so far into the segment (kept until it is complete). */
  buffer: string
  /** The segment is complete and focus should move on. */
  complete: boolean
}

/**
 * Type one digit into a segment. A leading digit that cannot start a two-digit
 * value (e.g. 4 for a day) completes the segment immediately as 04.
 */
export function typeDigit(
  parts: Record<SegmentKind, number>,
  kind: SegmentKind,
  buffer: string,
  digit: string,
): TypeResult {
  const typed = buffer + digit
  const width = kind === 'year' ? 4 : 2
  const max = LIMITS[kind][1]
  const result = { ...parts }

  if (kind === 'year') {
    result.year = Number(typed)
    return { parts: result, buffer: typed.length < 4 ? typed : '', complete: typed.length >= 4 }
  }

  const value = Number(typed)
  if (typed.length >= width || value * 10 > max) {
    // Values above the maximum keep only the last digit ("39" for a month → 09).
    result[kind] = value > max ? Number(digit) : value
    if (result[kind] < LIMITS[kind][0]) result[kind] = LIMITS[kind][0]
    return { parts: normalize(result), buffer: '', complete: true }
  }
  result[kind] = Math.max(value, kind === 'day' || kind === 'month' ? 0 : LIMITS[kind][0])
  return { parts: result, buffer: typed, complete: false }
}
