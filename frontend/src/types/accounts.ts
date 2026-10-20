import type { Id } from '@/types/common'
import type { NotificationKey } from './settings'
import type { Ref } from './common'
import type { LocationRef } from './masterdata'

export interface UserRef {
  id: Id
  username: string
  display_name: string
}

export interface User extends UserRef {
  first_name: string
  last_name: string
  email: string
  employee_number: string
  job_title: string
  phone: string
  department: Ref | null
  is_it_staff: boolean
  is_terminal: boolean
  /** Pickup terminal only: lists pickups at this location and below. */
  terminal_location: LocationRef | null
  is_active: boolean
  /** Directory account; synced fields are overwritten at every login. */
  is_ldap_user: boolean
}

export interface CurrentUser extends User {
  language: 'en' | 'de'
  /** Email notifications switched off by the user ({event: false}). */
  notification_settings: Partial<Record<NotificationKey, boolean>>
  /** The own dashboard layout; empty means the default. */
  dashboard_settings: DashboardSettings
  is_superuser: boolean
}

export type WidgetSize = 'small' | 'medium' | 'large'
/** `auto` fits the content and the row; the others are fixed heights that scroll. */
export type WidgetHeight = 'auto' | 'small' | 'medium' | 'large'

/** One dashboard widget as the user arranged it; the order of the list is the order on screen. */
export interface WidgetSettings {
  id: string
  visible: boolean
  size: WidgetSize
  height: WidgetHeight
  /** Cards of a key figure panel the user switched off. */
  hidden_cards: string[]
  /** Cards of a key figure panel in the user's order; empty keeps the default order. */
  card_order: string[]
  /** The widget's own settings, such as the text of the notes widget. */
  options: Record<string, unknown>
}

export interface DashboardSettings {
  widgets?: WidgetSettings[]
}

export interface Department {
  id: Id
  name: string
  code: string
  cost_center: string
  sort_order: number
  member_count: number
}

export interface TeamRef {
  id: Id
  name: string
  code: string
}

/** An IT work queue (e.g. support, Ledgerline); one person may be in several teams. */
export interface Team extends TeamRef {
  sort_order: number
  /** Members follow this directory group at sign-in; empty = maintained by hand. */
  ldap_group_dn: string
  /** Gets what no category or model routes elsewhere; only one team at a time. */
  is_default: boolean
  members: UserRef[]
}
