import type { Id } from '@/types/common'
import type { TeamRef, UserRef } from './accounts'
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
  asset_request: { id: Id; number: string; status: string; requester: UserRef } | null
  /** Assigned to this device directly. */
  consumables: AssetModelRef[]
  /** Compatible with the device's model. */
  model_consumables: AssetModelRef[]
  licenses: AssetLicense[]
  open_issues: OwnIssue[]
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

/** Several identical devices numbered in a row from the category's number sequence. */
export type AssetSeriesInput = Pick<
  AssetInput,
  | 'model'
  | 'condition'
  | 'is_loanable'
  | 'location'
  | 'supplier'
  | 'purchase_date'
  | 'purchase_price'
  | 'warranty_until'
  | 'notes'
> & { count: number | null }

export interface AssetSeriesPreview {
  sequence: string
  first: string
  last: string
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
  asset_request: { id: Id; number: string } | null
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

export type LicenseAssignTo = 'user' | 'device'

export interface License {
  id: Id
  model: AssetModelRef
  category: CategoryRef
  manufacturer: Ref
  reference: string
  license_key: string
  seats: number
  seats_used: number
  assign_to: LicenseAssignTo
  valid_from: string | null
  valid_until: string | null
  is_expired: boolean
  supplier: Ref | null
  purchase_date: string | null
  purchase_price: string | null
  notes: string
  created_at: string
  updated_at: string
}

export interface LicenseAssignment {
  id: Id
  user: UserRef | null
  asset: {
    id: Id
    inventory_number: string
    model: AssetModelRef
    assigned_to: UserRef | null
  } | null
  assigned_by: UserRef | null
  note: string
  created_at: string
}

export interface LicenseDetail extends License {
  assignments: LicenseAssignment[]
}

export interface LicenseInput {
  model: Id | null
  reference: string
  license_key: string
  seats: number
  assign_to: LicenseAssignTo
  valid_from: string | null
  valid_until: string | null
  supplier: Id | null
  purchase_date: string | null
  purchase_price: string | null
  notes: string
}

/** Software the employee uses, directly or through one of their devices (no key). */
export interface OwnLicense {
  id: Id
  model: AssetModelRef
  category_icon: string
  valid_until: string | null
  is_expired: boolean
  assigned_at: string
  device: { id: Id; inventory_number: string; model: AssetModelRef } | null
}

/** A license seat used by a device. */
export interface AssetLicense {
  id: Id
  model: AssetModelRef
  reference: string
  valid_until: string | null
}

export type IssueKind = 'defect' | 'damage' | 'lost' | 'other'
export const ISSUE_KINDS: IssueKind[] = ['defect', 'damage', 'lost', 'other']
export type IssueStatus = 'open' | 'in_progress' | 'resolved'
export const ISSUE_STATUSES: IssueStatus[] = ['open', 'in_progress', 'resolved']

/** A problem report as the reporting employee sees it. */
export interface OwnIssue {
  id: Id
  kind: IssueKind
  description: string
  status: IssueStatus
  created_at: string
  /** IT wrote or changed the status since the employee last looked. */
  unseen_update: boolean
  /** The latest message of either side. */
  last_message: string | null
}

/** One of the employee's reports in their list of all reports. */
export interface OwnIssueWithDevice extends OwnIssue {
  asset: { id: Id; inventory_number: string; model: AssetModelRef; category_icon: string }
  /** False once the device was returned; then there is no device page to open. */
  still_assigned: boolean
}

/** A problem report in the IT list. */
export interface AssetIssue extends Omit<OwnIssue, 'last_message'> {
  asset: { id: Id; inventory_number: string; model: AssetModelRef; assigned_to: UserRef | null }
  reported_by: UserRef | null
  handled_by: UserRef | null
  /** Responsible IT team and person; independent of each other, both optional. */
  assigned_team: TeamRef | null
  assignee: UserRef | null
  resolved_at: string | null
}

/** Which side a step in a report's conversation came from. */
export type IssueSide = 'reporter' | 'it'

/** A message or a change of status in a report's conversation. */
export interface IssueEntry {
  id: Id
  kind: 'message' | 'status'
  author: UserRef | null
  side: IssueSide
  text: string
  /** The new status of a status change. */
  status: IssueStatus | ''
  created_at: string
}

/** A report with its conversation, for its detail page (IT and reporter). */
export interface AssetIssueDetail {
  id: Id
  kind: IssueKind
  description: string
  status: IssueStatus
  created_at: string
  resolved_at: string | null
  reported_by: {
    id: Id
    display_name: string
    email: string
    phone: string
    job_title: string
    department: string | null
  } | null
  handled_by: UserRef | null
  assigned_team: TeamRef | null
  assignee: UserRef | null
  asset: {
    id: Id
    inventory_number: string
    serial_number: string
    hostname: string
    status: string
    model: AssetModelRef
    category: string
    category_icon: string
    assigned_to: UserRef | null
    assigned_since: string | null
    location: { id: Id; name: string; full_name: string } | null
    purchase_date: string | null
    warranty_until: string | null
  }
  entries: IssueEntry[]
  /** Other reports on the same device (for the reporter: only their own). */
  other_issues: {
    id: Id
    kind: IssueKind
    description: string
    status: IssueStatus
    created_at: string
  }[]
  unseen_update: boolean
  /** The reporter still has the device. */
  still_assigned: boolean
}
