import type { Id } from '@/types/common'
import type { Ref } from './common'

export type Tracking = 'serialized' | 'bulk'

export interface AssetModelRef {
  id: Id
  name: string
  full_name: string
  tracking: Tracking
}

export interface CategoryRef {
  id: Id
  name: string
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
  code: string
  parent: Ref | null
  description: string
  icon: string
  number_sequence: Ref | null
  is_requestable: boolean
  allow_any_model: boolean
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
  preview: string
}
