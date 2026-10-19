import { CalendarClock, PackageCheck, ShieldAlert, Truck, Undo2 } from '@lucide/vue'
import type { Component } from 'vue'

import type { CalendarEntry, CalendarKind } from '@/types/calendar'

export const KIND_ICONS: Record<CalendarKind, Component> = {
  loan: CalendarClock,
  pickup: PackageCheck,
  return: Undo2,
  delivery: Truck,
  warranty: ShieldAlert,
}

/** One colour per kind (matching the filter chips), from the app palette. */
const KIND_COLORS: Record<CalendarKind, string> = {
  loan: 'var(--ar-primary)',
  pickup: 'var(--ar-success)',
  return: 'var(--ar-info)',
  delivery: 'var(--ar-warning)',
  warranty: 'var(--ar-violet)',
}

export const kindColor = (kind: CalendarKind) => KIND_COLORS[kind]

/** Overdue returns and lendings stand out in red regardless of their kind. */
export function entryColor(entry: Pick<CalendarEntry, 'kind' | 'overdue'>): string {
  return entry.overdue ? 'var(--ar-error)' : KIND_COLORS[entry.kind]
}

/**
 * Not settled yet: a request IT has not approved, or a pickup whose devices are
 * not prepared. Drawn as outline only; everything confirmed is filled.
 */
export function isTentative(entry: Pick<CalendarEntry, 'kind' | 'status'>): boolean {
  return (
    (entry.kind === 'loan' && entry.status === 'submitted') ||
    (entry.kind === 'pickup' && entry.status === 'approved')
  )
}
