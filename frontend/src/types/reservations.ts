import type { Id } from '@/types/common'
import type { TeamRef, UserRef } from './accounts'
import type { Ref } from './common'
import type { AssetRef, OwnIssue } from './inventory'
import type { AssetModelRef, CategoryKind, CategoryRef, LocationRef } from './masterdata'

export type ReservationStatus =
  'submitted' | 'approved' | 'ready' | 'handed_out' | 'completed' | 'rejected' | 'cancelled'

export type Duration = 'temporary' | 'permanent'
export type HandoverMode = 'pickup' | 'collect' | 'delivery'
export type HandoverMethod = 'signature' | 'delivered' | 'direct'

export const RESERVATION_STATUSES: ReservationStatus[] = [
  'submitted',
  'approved',
  'ready',
  'handed_out',
  'completed',
  'rejected',
  'cancelled',
]

/** A license seat allocated to a request; device licenses name the device. */
export interface LicenseSeat {
  id: Id
  model: AssetModelRef
  reference: string
  valid_until: string | null
  device: AssetRef | null
}

export interface Allocation {
  id: Id
  asset: AssetRef | null
  consumable: { id: Id; model: AssetModelRef; location: LocationRef } | null
  license: LicenseSeat | null
  quantity: number
  allocated_by: UserRef | null
  allocated_at: string
  handout_note: string
  handed_out_at: string | null
  returned_at: string | null
  /** The return record it came back with. */
  device_return: Id | null
  returned_damaged: boolean
  return_note: string
  category_icon: string
}

export interface ReservationItem {
  id: Id
  label: string
  category: CategoryRef | null
  asset_model: AssetModelRef | null
  description: string
  is_free_text: boolean
  /** Software lines are filled with license seats instead of devices. */
  is_software: boolean
  quantity_requested: number
  quantity_approved: number | null
  quantity_allocated: number
  quantity_missing: number
  note: string
  allocations: Allocation[]
}

export interface ReservationListItem {
  id: Id
  number: string
  title: string
  requester: UserRef
  department: Ref | null
  duration: Duration
  start_date: string
  end_date: string | null
  status: ReservationStatus
  handover_mode: HandoverMode
  /** The employee's preferred pickup day; IT sets the appointment (pickup_at). */
  requested_pickup_date?: string | null
  /** The terminal starts with who collects (set when marking ready). */
  skip_device_check: boolean
  is_overdue: boolean
  pickup_at: string | null
  item_count: number
  unit_count: number
  summary: string
  created_at: string
  /** Responsible IT team and person; independent of each other, both optional. IT only. */
  assigned_team: TeamRef | null
  assignee: UserRef | null
}

export interface Handover {
  method: HandoverMethod
  received_by: UserRef | null
  received_by_name: string
  signature: string
  notes: string
  location: string
  /** IT member responsible; at the terminal whoever prepared the pickup unless changed. */
  handed_out_by: UserRef | null
  /** The account the hand-out was recorded with, e.g. the pickup terminal. */
  recorded_by: UserRef | null
  handed_out_at: string
}

export interface DeviceReturn {
  id: Id
  notes: string
  returned_by: UserRef | null
  returned_at: string
}

export interface Reservation extends ReservationListItem {
  notes: string
  pickup_location: LocationRef | null
  it_comment: string
  created_by: UserRef | null
  handled_by: UserRef | null
  prepared_by: UserRef | null
  approved_at: string | null
  handed_out_at: string | null
  completed_at: string | null
  items: ReservationItem[]
  handover: Handover | null
  returns: DeviceReturn[]
}

export interface ReservationItemInput {
  category?: Id | null
  asset_model?: Id | null
  description?: string
  quantity: number
  note?: string
}

export interface ReservationInput {
  title: string
  notes: string
  duration: Duration
  start_date: string
  end_date: string | null
  requested_pickup_date: string | null
  items: ReservationItemInput[]
  requester?: Id | null
}

export interface Candidates {
  assets: {
    id: Id
    inventory_number: string
    serial_number: string
    condition: string
    model: AssetModelRef
    location: LocationRef | null
  }[]
  consumables: { id: Id; model: AssetModelRef; location: LocationRef; available_quantity: number }[]
  licenses?: {
    id: Id
    model: AssetModelRef
    reference: string
    assign_to: 'user' | 'device'
    valid_until: string | null
    free_seats: number
  }[]
  /** The requester's devices, for licenses that are assigned to a device. */
  devices?: AssetRef[]
}

export interface CatalogModel {
  id: Id
  name: string
  full_name: string
  tracking: string
  description: string
  /** Free in the chosen period; IT staff only, otherwise null. */
  available: number | null
  /** Promised to other requests in that period. */
  reserved: number | null
}

export interface CatalogCategory {
  id: Id
  name: string
  kind: CategoryKind
  item_name: string
  code: string
  icon: string
  description: string
  parent_id: Id | null
  allow_any_model: boolean
  /** Own models only, including requests for any device of the category. */
  available: number | null
  reserved: number | null
  models: CatalogModel[]
}

export interface AvailabilityCounts {
  available: number
  reserved: number
}

export interface PeriodAvailability {
  models: Record<Id, AvailabilityCounts>
  categories: Record<Id, AvailabilityCounts>
}

/** The period of a request; availability in the catalog refers to it. */
export type PeriodQuery = {
  start: string
  end?: string
  permanent?: boolean
}

export interface MyAsset {
  id: Id
  inventory_number: string
  serial_number: string
  model: AssetModelRef
  category: string
  category_icon: string
  assigned_since: string | null
  reservation_number: string | null
  return_due: string | null
  issues: OwnIssue[]
}

/** Consumables that fit one of the employee's devices (quick pick when requesting). */
export interface MyConsumables {
  asset: { id: Id; inventory_number: string; model: AssetModelRef }
  consumables: AssetModelRef[]
}

export interface TerminalPerson {
  id: Id
  display_name: string
  employee_number: string
  department: Ref | null
}

export interface TerminalPickup {
  id: Id
  number: string
  title: string
  requester: TerminalPerson
  pickup_at: string | null
  pickup_location: LocationRef | null
  unit_count: number
  summary: string
}

export interface HandOutInput {
  method: 'direct' | 'delivered'
  received_by: Id | null
  received_by_name: string
  location: string
  notes: string
  allocation_notes: { allocation: Id; note: string }[]
}

export interface SignInput {
  /** IT member handing out; left out, whoever prepared the pickup. */
  handed_out_by?: Id | null
  received_by: Id | null
  received_by_name: string
  signature: string
  notes: string
  allocation_notes: { allocation: Id; note: string }[]
}

export interface ReturnInput {
  /** Left out: everything still lent. */
  allocations: Id[] | null
  notes: string
  allocation_notes: { allocation: Id; note: string }[]
  /** Devices that go to repair instead of back into stock. */
  damaged: Id[]
}

export interface TerminalStaff {
  id: Id
  display_name: string
}
