import type { Id } from '@/types/common'
import type { UserRef } from './accounts'
import type { Ref } from './common'
import type { AssetModelRef, CategoryRef, LocationRef } from './masterdata'
import type { ReservationStatus } from './reservations'

export type OrderStatus = 'draft' | 'ordered' | 'partially_received' | 'received' | 'cancelled'

export const ORDER_STATUSES: OrderStatus[] = [
  'draft',
  'ordered',
  'partially_received',
  'received',
  'cancelled',
]

export interface OrderLine {
  id: Id
  label: string
  asset_model: AssetModelRef | null
  description: string
  quantity: number
  quantity_received: number
  quantity_open: number
  unit_price: string | null
  total: string
  reservation_item: {
    id: Id
    label: string
    reservation: { id: Id; number: string; requester: UserRef }
  } | null
}

export interface OrderListItem {
  id: Id
  number: string
  supplier: Ref | null
  status: OrderStatus
  order_date: string | null
  expected_date: string | null
  supplier_reference: string
  total: string
  line_count: number
  created_at: string
}

export interface Order extends OrderListItem {
  delivery_location: LocationRef | null
  notes: string
  created_by: UserRef | null
  lines: OrderLine[]
}

export interface OrderLineInput {
  id?: Id | null
  asset_model: Id | null
  description: string
  quantity: number
  unit_price: string | null
  reservation_item?: Id | null
}

export interface OrderInput {
  supplier: Id | null
  expected_date: string | null
  supplier_reference: string
  delivery_location: Id | null
  notes: string
  lines?: OrderLineInput[]
}

export interface ReservationNeed {
  reservation_item: {
    id: Id
    label: string
    is_free_text: boolean
    category: CategoryRef | null
    asset_model: AssetModelRef | null
    default_supplier: Ref | null
  }
  reservation: {
    id: Id
    number: string
    title: string
    status: ReservationStatus
    start_date: string
    requester: UserRef
  }
  missing: number
  available: number
  on_order: number
  to_order: number
}

export interface ConsumableNeed {
  consumable: {
    id: Id
    model: AssetModelRef
    location: LocationRef
    quantity: number
    min_quantity: number
    default_supplier: Ref | null
  }
  missing: number
  on_order: number
  to_order: number
}

export interface Needs {
  reservations: ReservationNeed[]
  consumables: ConsumableNeed[]
}
