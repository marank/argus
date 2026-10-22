import type { TeamRef } from './accounts'
import type { Id } from '@/types/common'
import type { Ref } from './common'

export type Tracking = 'serialized' | 'bulk' | 'license'

export type CategoryKind = 'hardware' | 'software'
export const CATEGORY_KINDS: CategoryKind[] = ['hardware', 'software']

export interface AssetModelRef {
  id: Id
  name: string
  designation: string
  full_name: string
  tracking: Tracking
}

export interface CategoryRef {
  id: Id
  name: string
  kind: CategoryKind
  /** Singular, e.g. "Laptop"; may be empty. */
  item_name: string
  code: string
  icon: string
}

export interface LocationRef {
  id: Id
  name: string
  full_name: string
}

export interface Manufacturer {
  id: Id
  name: string
  website: string
  support_url: string
  support_phone: string
  notes: string
  is_active: boolean
}

export interface Supplier {
  id: Id
  name: string
  customer_number: string
  contact_person: string
  email: string
  phone: string
  website: string
  address: string
  notes: string
  is_active: boolean
}

export interface Category {
  id: Id
  name: string
  kind: CategoryKind
  item_name: string
  code: string
  parent: Ref | null
  description: string
  icon: string
  number_sequence: Ref | null
  /** Gets new requests and reports; empty = as the parent. IT only. */
  team: TeamRef | null
  /** The own team, the nearest parent's, otherwise the default team. IT only. */
  effective_team: TeamRef | null
  is_requestable: boolean
  allow_any_model: boolean
  /** The requester's department approves first; applies to subcategories too. */
  requires_approval: boolean
  /** Approval required here or by a category above. */
  needs_approval: boolean
  sort_order: number
  path: string[]
}

export interface Location {
  id: Id
  name: string
  full_name: string
  code: string
  kind: 'site' | 'building' | 'room' | 'storage'
  parent: Ref | null
  description: string
  is_pickup_point: boolean
}

export interface AssetModel {
  id: Id
  name: string
  /** The manufacturer's own name for the model; unique per manufacturer. */
  designation: string
  full_name: string
  manufacturer: Ref
  category: CategoryRef
  part_number: string
  ean: string
  tracking: Tracking
  description: string
  specifications: string
  default_supplier: Ref | null
  list_price: string | null
  warranty_months: number
  compatible_with: AssetModelRef[]
  /** Inventory numbers for new devices; empty = the category's, otherwise the general one. */
  number_sequence: Ref | null
  /** The sequence that applies: own, the category's or the general one; empty unless individual devices. */
  effective_number_sequence: Ref | null
  /** Gets new requests and reports; empty = as the category. IT only. */
  team: TeamRef | null
  /** The own team, the category's (or a parent's), otherwise the default team. IT only. */
  effective_team: TeamRef | null
  is_requestable: boolean
  is_active: boolean
}

export interface NumberSequence {
  id: Id
  code: string
  name: string
  prefix: string
  pattern: string
  padding: number
  next_value: number
  reset_period: 'never' | 'yearly' | 'monthly'
  /** Argus draws inventory, request or order numbers from it; code fixed, not deletable. */
  is_system: boolean
  preview: string
}
