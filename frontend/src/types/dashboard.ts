import type { Id } from '@/types/common'
import type { UserRef } from './accounts'
import type { AssetEventWithAsset } from './inventory'

export interface ITOverview {
  asset_status: Record<string, number>
  reservations_submitted: number
  reservations_to_prepare: number
  reservations_ready: number
  reservations_overdue: number
  orders_to_place: number
  orders_in_transit: number
  low_consumables: number
  warranty_expiring: number
  upcoming: {
    id: Id
    number: string
    title: string
    status: string
    start_date: string
    pickup_at: string | null
    requester: UserRef
  }[]
  recent_events: AssetEventWithAsset[]
}

export interface EmployeeOverview {
  open_reservations: number
  ready_for_pickup: { id: Id; number: string; title: string; pickup_at: string | null }[]
  assigned_assets: number
}
