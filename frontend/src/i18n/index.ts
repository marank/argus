import { createI18n } from 'vue-i18n'

import de from './locales/de'
import en from './locales/en'

export type Locale = 'en' | 'de'
export type MessageSchema = typeof en

/**
 * The same in both languages; the locale gives the wording and order. Dates
 * with a weekday are put together from the parts in `useFormat`, which reads
 * better than the browser's "Di., 20. Okt., 13:33".
 */
const DATETIME_FORMATS = {
  date: { year: 'numeric', month: '2-digit', day: '2-digit' },
  time: { hour: '2-digit', minute: '2-digit' },
  dateTime: {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  },
  weekdayShort: { weekday: 'short' },
  weekdayLong: { weekday: 'long' },
  /** "20. Okt." / "Oct 20" */
  dayMonth: { day: 'numeric', month: 'short' },
  /** "20. Oktober" / "October 20" */
  dayMonthLong: { day: 'numeric', month: 'long' },
} as const

const stored = localStorage.getItem('argus.locale') as Locale | null
const browser = navigator.language.startsWith('de') ? 'de' : 'en'

export const i18n = createI18n<[MessageSchema], Locale, false>({
  legacy: false,
  locale: stored ?? browser,
  fallbackLocale: 'en',
  messages: { en, de },
  datetimeFormats: { en: DATETIME_FORMATS, de: DATETIME_FORMATS },
  numberFormats: {
    en: { currency: { style: 'currency', currency: 'EUR' } },
    de: { currency: { style: 'currency', currency: 'EUR' } },
  },
})

export function setLocale(locale: Locale) {
  i18n.global.locale.value = locale
  localStorage.setItem('argus.locale', locale)
  document.documentElement.lang = locale
}

document.documentElement.lang = i18n.global.locale.value
