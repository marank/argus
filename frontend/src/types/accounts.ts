import type { Id } from '@/types/common'
import type { NotificationKey } from './settings'
import type { Ref } from './common'

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
  is_active: boolean
  /** Directory account; synced fields are overwritten at every login. */
  is_ldap_user: boolean
}

export interface CurrentUser extends User {
  language: 'en' | 'de'
  /** Email notifications switched off by the user ({event: false}). */
  notification_settings: Partial<Record<NotificationKey, boolean>>
  is_superuser: boolean
}

export interface Department {
  id: Id
  name: string
  code: string
  cost_center: string
  sort_order: number
  member_count: number
}
