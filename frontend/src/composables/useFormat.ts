import { useI18n } from 'vue-i18n'

/** Locale-aware formatting helpers for dates, money and enum labels. */
export function useFormat() {
  const { d, n, t, te } = useI18n()

  const toDate = (value: string) => new Date(value.length === 10 ? `${value}T00:00:00` : value)

  return {
    date: (value: string | null | undefined) => (value ? d(toDate(value), 'date') : '—'),
    dateTime: (value: string | null | undefined) => (value ? d(toDate(value), 'dateTime') : '—'),
    weekday: (value: string | null | undefined) => (value ? d(toDate(value), 'weekday') : '—'),
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
