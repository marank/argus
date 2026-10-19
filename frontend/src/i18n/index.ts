import { createI18n } from 'vue-i18n'

import de from './locales/de'
import en from './locales/en'

export type Locale = 'en' | 'de'
export type MessageSchema = typeof en

export const SUPPORTED_LOCALES: Locale[] = ['en', 'de']

const stored = localStorage.getItem('argus.locale') as Locale | null
const browser = navigator.language.startsWith('de') ? 'de' : 'en'

export const i18n = createI18n<[MessageSchema], Locale, false>({
  legacy: false,
  locale: stored ?? browser,
  fallbackLocale: 'en',
  messages: { en, de },
  datetimeFormats: {
    en: {
      date: { year: 'numeric', month: '2-digit', day: '2-digit' },
      dateTime: {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      },
      weekday: {
        weekday: 'short',
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      },
    },
    de: {
      date: { year: 'numeric', month: '2-digit', day: '2-digit' },
      dateTime: {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      },
      weekday: {
        weekday: 'short',
        day: '2-digit',
        month: 'short',
        hour: '2-digit',
        minute: '2-digit',
      },
    },
  },
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
