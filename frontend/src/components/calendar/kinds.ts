import { CalendarClock, KeyRound, PackageCheck, ShieldAlert, Truck, Undo2 } from '@lucide/vue'
import type { Component } from 'vue'
import type { RouteLocationRaw } from 'vue-router'

import type { CalendarEntry, CalendarKind } from '@/types/calendar'

export const KIND_ICONS: Record<CalendarKind, Component> = {
  loan: CalendarClock,
  pickup: PackageCheck,
  return: Undo2,
  delivery: Truck,
  warranty: ShieldAlert,
  license: KeyRound,
}

/** One colour per kind (matching the filter chips), from the app palette. */
const KIND_COLORS: Record<CalendarKind, string> = {
  loan: 'var(--ar-primary)',
  pickup: 'var(--ar-success)',
  return: 'var(--ar-info)',
  delivery: 'var(--ar-warning)',
  warranty: 'var(--ar-violet)',
  license: 'var(--ar-pink)',
}

export const kindColor = (kind: CalendarKind) => KIND_COLORS[kind]

/** Overdue returns and lendings stand out in red regardless of their kind. */
export function entryColor(entry: Pick<CalendarEntry, 'kind' | 'overdue'>): string {
  return entry.overdue ? 'var(--ar-error)' : KIND_COLORS[entry.kind]
}

/**
 * Not settled yet: a request IT has not confirmed, or a pickup whose devices are
 * not prepared. Drawn as outline only; everything confirmed is filled.
 */
export function isTentative(entry: Pick<CalendarEntry, 'kind' | 'status'>): boolean {
  return (
    (entry.kind === 'loan' && ['pending_approval', 'submitted'].includes(entry.status)) ||
    (entry.kind === 'pickup' && entry.status === 'confirmed')
  )
}

type Translate = (key: string, named: Record<string, unknown>, plural?: number) => string

/** The text shown for an entry; the API sends only the name, number or supplier. */
export function entryLabel(entry: CalendarEntry, t: Translate): string {
  switch (entry.kind) {
    case 'pickup':
      return t('calendar.titles.pickup', { name: entry.title })
    case 'return':
      return t('calendar.titles.return', { name: entry.title })
    case 'delivery':
      return t('calendar.titles.delivery', { supplier: entry.title })
    case 'warranty':
      return t('calendar.titles.warranty', { count: Number(entry.title) }, Number(entry.title))
    case 'license':
      return t('calendar.titles.license', { name: entry.title })
    default:
      return entry.title
  }
}

/** Where an entry leads: its request, order or license, or the devices whose warranty ends. */
export function entryRoute(entry: CalendarEntry): RouteLocationRaw | null {
  if (entry.link.name === 'assets')
    return { name: 'assets', query: { warranty_until: entry.link.warranty_until } }
  if (entry.link.id) return { name: entry.link.name, params: { id: entry.link.id } }
  return null
}
