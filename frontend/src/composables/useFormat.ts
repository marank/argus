import { useI18n } from 'vue-i18n'

/** Locale-aware formatting helpers for dates, money and enum labels. */
/** Midnight of the day, so day differences ignore the time and DST shifts. */
const startOfDay = (date: Date) =>
  new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime()

export function useFormat() {
  // eslint-disable-next-line @typescript-eslint/unbound-method -- vue-i18n binds its composer functions
  const { d, n, t, te } = useI18n()

  const isDateOnly = (value: string) => value.length === 10
  const toDate = (value: string) => new Date(isDateOnly(value) ? `${value}T00:00:00` : value)

  /**
   * Weekday, date and time put together, e.g. "Di 20. Okt. · 13:33": the
   * weekday without its abbreviation dot, the time set off by a middle dot.
   */
  function withWeekday(at: Date, weekday: string, date: string, time: boolean) {
    const day = `${d(at, weekday).replace(/\.$/, '')} ${d(at, date)}`
    return time ? `${day} · ${d(at, 'time')}` : day
  }
  /** Plain dates ("2026-10-20") have no time to show. */
  const parse = (value: string | Date) =>
    typeof value === 'string'
      ? { at: toDate(value), time: !isDateOnly(value) }
      : { at: value, time: true }

  return {
    date: (value: string | null | undefined) => (value ? d(toDate(value), 'date') : '—'),
    dateTime: (value: string | null | undefined) => (value ? d(toDate(value), 'dateTime') : '—'),
    /** Like `date` / `dateTime` with the short weekday in front, e.g. "Di 20.10.2026 · 12:00". */
    dateWithWeekday: (value: string | null | undefined) => {
      if (!value) return '—'
      const { at, time } = parse(value)
      return withWeekday(at, 'weekdayShort', 'date', time)
    },
    /** For headings, e.g. "Dienstag, 20. Oktober · 13:33"; the time only where asked for. */
    longDate: (value: string | Date, withTime = false) => {
      const { at, time } = parse(value)
      const day = `${d(at, 'weekdayLong')}, ${d(at, 'dayMonthLong')}`
      return withTime && time ? `${day} · ${d(at, 'time')}` : day
    },
    /**
     * How far away a day is, e.g. "Morgen, 20:00 Uhr" or "In 2 Tagen"; with the
     * time only when the value has one.
     */
    relativeDay: (value: string | null | undefined) => {
      if (!value) return '—'
      const at = toDate(value)
      const days = Math.round((startOfDay(at) - startOfDay(new Date())) / 86_400_000)
      const day =
        days === 0
          ? t('common.relative.today')
          : days === 1
            ? t('common.relative.tomorrow')
            : days === -1
              ? t('common.relative.yesterday')
              : days > 0
                ? t('common.relative.inDays', { count: days })
                : t('common.relative.daysAgo', { count: -days })
      return isDateOnly(value) ? day : t('common.relative.atTime', { day, time: d(at, 'time') })
    },
    /** Weekday and date, e.g. "Di 20. Okt. · 13:33"; the time only when the value has one. */
    weekday: (value: string | Date | null | undefined) => {
      if (!value) return '—'
      const { at, time } = parse(value)
      return withWeekday(at, 'weekdayShort', 'dayMonth', time)
    },
    money: (value: string | number | null | undefined) =>
      value === null || value === undefined || value === '' ? '—' : n(Number(value), 'currency'),
    /** Translate an enum value, e.g. `enumLabel('assetStatus', 'in_use')`. */
    enumLabel: (group: string, value: string | null | undefined) => {
      if (!value) return '—'
      const key = `enums.${group}.${value}`
      return te(key) ? t(key) : value
    },
  }
}

/** ISO date (YYYY-MM-DD) in local time, as the API expects. */
export function toIsoDate(value: number | Date | null | undefined): string | null {
  if (value === null || value === undefined) return null
  const date = new Date(value)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`
}

export function fromIsoDate(value: string | null | undefined): number | null {
  return value ? new Date(`${value}T00:00:00`).getTime() : null
}
