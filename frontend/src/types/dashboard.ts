import type { Id, Ref } from '@/types/common'
import type { UserRef } from './accounts'
import type { AssetEventWithAsset, AssetRef } from './inventory'
import type { AssetModelRef, LocationRef } from './masterdata'

export interface ITOverview {
  asset_status: Record<string, number>
  reservations_submitted: number
  reservations_to_prepare: number
  reservations_ready: number
  reservations_overdue: number
  orders_to_place: number
  orders_in_transit: number
  low_consumables: number
  open_issues: number
  /** Open requests and reports by who is responsible, from the viewer's side. */
  requests_mine: number
  requests_my_teams: number
  requests_unassigned: number
  issues_mine: number
  warranty_expiring: number
  licenses_expiring: number
  recent_events: AssetEventWithAsset[]
}

export interface EmployeeOverview {
  open_reservations: number
  ready_for_pickup: { id: Id; number: string; title: string; pickup_at: string | null }[]
  assigned_assets: number
}

/** Props every dashboard widget component gets. */
export interface WidgetProps {
  data: ITOverview
  /** The widget's own stored settings; changed by emitting `update:options`. */
  options: Record<string, unknown>
}

export interface TaskRequest {
  id: Id
  number: string
  title: string
  status: string
  start_date: string
  end_date: string | null
  requester: UserRef
}

export interface TaskIssue {
  id: Id
  kind: string
  status: string
  description: string
  created_at: string
  asset: AssetRef
  reported_by: UserRef | null
}

export interface MyTasks {
  requests: TaskRequest[]
  requests_total: number
  issues: TaskIssue[]
  issues_total: number
}

export interface OverdueReturn {
  id: Id
  number: string
  title: string
  end_date: string
  requester: UserRef
  /** The employee has an email address a reminder can go to. */
  can_remind: boolean
  reminded_at: string | null
  reminded_by: UserRef | null
}

export interface TeamLoad {
  people: { user: UserRef; requests: number; issues: number }[]
  unassigned_requests: number
  unassigned_issues: number
}

export interface TrendWeek {
  /** Monday of the week. */
  week_start: string
  created: number
  completed: number
}

export interface UpcomingHandout {
  id: Id
  number: string
  title: string
  status: string
  start_date: string
  pickup_at: string | null
  requester: UserRef
}

/** A lending that ends soon; same fields as an overdue one. */
export type DueReturn = OverdueReturn

export interface ExpiringItem {
  kind: 'license' | 'warranty'
  /** The license, or the device whose warranty ends. */
  id: Id
  label: string
  detail: string
  ends_on: string
}

export interface LowStockItem {
  id: Id
  model: AssetModelRef
  location: LocationRef
  quantity: number
  min_quantity: number
}

export interface OpenOrder {
  id: Id
  number: string
  status: string
  supplier: Ref | null
  order_date: string | null
  expected_date: string | null
}

export interface WaitingRequest {
  id: Id
  number: string
  title: string
  start_date: string
  created_at: string
  requester: UserRef
  assignee: UserRef | null
}
