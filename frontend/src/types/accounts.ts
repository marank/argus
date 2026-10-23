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
  /** Administrator: all rights; only administrators appoint administrators. */
  is_superuser: boolean
  is_terminal: boolean
  /** Pickup terminal only: lists pickups at this location and below. */
  terminal_location: LocationRef | null
  is_active: boolean
  /** Requests go straight to IT, even for categories that need approval. */
  approval_exempt: boolean
  /** Directory account; synced fields are overwritten at every login. */
  is_ldap_user: boolean
  /** Second sign-in step; only sent to IT staff and the user themself. */
  two_factor: TwoFactorMethod | null
  /** Roles of IT staff; only sent to IT staff. */
  roles: Ref[]
  /** Teams of IT staff; only sent to IT staff. */
  teams: Ref[]
}

/** Areas of the app that roles grant rights on (see backend apps.accounts.permissions). */
export type PermissionKey =
  | 'models'
  | 'categories'
  | 'manufacturers'
  | 'suppliers'
  | 'locations'
  | 'departments'
  | 'teams'
  | 'users'
  | 'number_sequences'
  | 'requests'
  | 'assets'
  | 'consumables'
  | 'licenses'
  | 'issues'
  | 'procurement'
export type PermissionLevel = 'read' | 'write'

/** A set of rights for IT staff; staff can hold several roles, their rights add up. */
export interface Role {
  id: Id
  name: string
  description: string
  /** Areas left out are not accessible. */
  permissions: Partial<Record<PermissionKey, PermissionLevel>>
  members: UserRef[]
}

export interface PermissionResource {
  key: PermissionKey
  group: 'masterdata' | 'operations'
}

export type TwoFactorMethod = 'email' | 'totp'

/** Answer of the login when the second sign-in step is due. */
export interface TwoFactorChallenge {
  two_factor: TwoFactorMethod
  /** Email method: where the code went (`m***@example.com`) and whether it went out. */
  email_hint: string
  code_sent: boolean
}

export interface TwoFactorStatus {
  method: TwoFactorMethod | null
  backup_codes_left: number
  /** Codes by email can reach the user (address set, mail sending configured). */
  email_available: boolean
  email_hint: string
}

export interface TwoFactorSetup {
  method: TwoFactorMethod
  /** Authenticator app: the secret, the otpauth link and it as QR code (SVG data URI). */
  secret: string
  uri: string
  qr_svg: string
  /** Email: where the confirmation code went. */
  email_hint: string
  code_sent: boolean
}

export interface CurrentUser extends User {
  language: 'en' | 'de'
  /** Email notifications switched off by the user ({event: false}). */
  /** Notifications switched off, by email and in the app ({kind: false}). */
  notification_settings: Partial<Record<NotificationKey, boolean>>
  app_notification_settings: Partial<Record<NotificationKey, boolean>>
  /** The own dashboard layout; empty means the default. */
  dashboard_settings: DashboardSettings
  /** Approves requests for at least one department. */
  is_approver: boolean
  /** Rights from the user's roles; everything for administrators. */
  permissions: Partial<Record<PermissionKey, PermissionLevel>>
}

export type WidgetSize = 'small' | 'medium' | 'large'
/** `auto` fits the content and the row; the others are fixed heights that scroll. */
export type WidgetHeight = 'auto' | 'small' | 'medium' | 'large'

/** One dashboard widget as the user arranged it; the order of the list is the order on screen. */
export interface WidgetSettings {
  id: string
  /** Set on further instances of a widget: which widget it is (the first has its id). */
  widget?: string
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
  parent: Ref | null
  /** Names from the top-level department down to this one. */
  path: string[]
  sort_order: number
  member_count: number
  /** Approve requests for categories that need approval; none = the parent's, else straight to IT. */
  approvers: UserRef[]
  /** The approvers that decide: the own or those taken over from a department above. */
  effective_approvers: UserRef[]
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
