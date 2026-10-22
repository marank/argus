import { describe, expect, it } from 'vitest'

import type { Reservation, ReservationEvent } from '@/types/reservations'
import { handoverPlanned } from '@/utils/reservations'

const withEvents = (...kinds: ReservationEvent['kind'][]) =>
  ({
    events: kinds.map((kind) => ({ kind }) as ReservationEvent),
    pickup_at: null,
  }) as Pick<Reservation, 'events' | 'pickup_at'>

describe('handoverPlanned', () => {
  it('is not planned for a direct hand-out that was only recorded and allocated', () => {
    expect(handoverPlanned(withEvents('direct', 'allocated'))).toBe(false)
  })

  it('is not planned by confirming: that only tells the employee it is fine', () => {
    expect(handoverPlanned(withEvents('created'))).toBe(false)
    expect(handoverPlanned(withEvents('created', 'confirmed', 'allocated'))).toBe(false)
  })

  it('is planned once marked ready or the handover was changed', () => {
    expect(handoverPlanned(withEvents('direct', 'allocated', 'ready', 'reopened'))).toBe(true)
    expect(handoverPlanned(withEvents('created', 'confirmed', 'rescheduled'))).toBe(true)
  })

  it('counts a date set when confirming older requests', () => {
    const older = { ...withEvents('created', 'confirmed'), pickup_at: '2026-10-20T09:00:00Z' }
    expect(handoverPlanned(older)).toBe(true)
  })
})
