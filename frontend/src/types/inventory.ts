import type { Id } from '@/types/common'
import type { UserRef } from './accounts'
import type { Ref } from './common'
import type { AssetModel, AssetModelRef, CategoryRef, LocationRef } from './masterdata'

export type AssetStatus = 'in_stock' | 'reserved' | 'in_use' | 'in_repair' | 'lost' | 'retired'
export type AssetCondition = 'new' | 'good' | 'worn' | 'defective'

export const ASSET_STATUSES: AssetStatus[] = [
  'in_stock',
  'reserved',
  'in_use',
  'in_repair',
  'lost',
  'retired',
]
export const ASSET_CONDITIONS: AssetCondition[] = ['new', 'good', 'worn', 'defective']

export interface AssetRef {
  id: Id
  inventory_number: string
  serial_number: string
  status: AssetStatus
  model: AssetModelRef
}

export interface Asset {
  id: Id
  inventory_number: string
  model: AssetModelRef
  category: CategoryRef
  manufacturer: Ref
  serial_number: string
  imei: string
  mac_address: string
  hostname: string
  status: AssetStatus
  condition: AssetCondition
  is_loanable: boolean
  location: LocationRef | null
  assigned_to: UserRef | null
  assigned_since: string | null
  parent: { id: Id; inventory_number: string } | null
  supplier: Ref | null
  purchase_date: string | null
  purchase_price: string | null
  warranty_until: string | null
  notes: string
  created_at: string
  updated_at: string
}

export interface AssetDetail extends Asset {
  components: { id: Id; inventory_number: string }[]
  reservation: { id: Id; number: string; status: string; requester: UserRef } | null
  /** Assigned to this device directly. */
  consumables: AssetModelRef[]
  /** Compatible with the device's model. */
  model_consumables: AssetModelRef[]
}

export interface AssetInput {
  model: Id | null
  inventory_number: string
  serial_number: string
  imei: string
  mac_address: string
  hostname: string
  status: AssetStatus
  condition: AssetCondition
  is_loanable: boolean
  location: Id | null
  assigned_to: Id | null
  parent: Id | null
  supplier: Id | null
  purchase_date: string | null
  purchase_price: string | null
  warranty_until: string | null
  consumables: Id[]
  notes: string
}

export type AssetEventKind =
  | 'created'
  | 'status_changed'
  | 'assigned'
  | 'returned'
  | 'reserved'
  | 'battery_replaced'
  | 'component_replaced'
  | 'repair'
  | 'maintenance'
  | 'inspection'
  | 'note'

export const MANUAL_EVENT_KINDS: AssetEventKind[] = [
  'battery_replaced',
  'component_replaced',
  'repair',
  'maintenance',
  'inspection',
  'note',
]

export interface AssetEvent {
  id: Id
  kind: AssetEventKind
  occurred_at: string
  description: string
  component: string
  component_serial: string
  cost: string | null
  performed_by: UserRef | null
  related_user: UserRef | null
  reservation: { id: Id; number: string } | null
}

export interface AssetEventWithAsset extends AssetEvent {
  asset: AssetRef
}

export interface Consumable {
  id: Id
  model: AssetModelRef
  category: CategoryRef
  location: LocationRef
  quantity: number
  reserved_quantity: number
  available_quantity: number
  min_quantity: number
  is_below_minimum: boolean
}

export type ConsumableReason = 'receipt' | 'issue' | 'return' | 'adjustment' | 'consumption'

export interface ConsumableMovement {
  id: Id
  delta: number
  reason: ConsumableReason
  note: string
  performed_by: UserRef | null
  recipient: UserRef | null
  created_at: string
}

export interface LookupResult {
  kind: 'asset' | 'model' | 'multiple' | 'none'
  assets: Asset[]
  models: AssetModel[]
}
