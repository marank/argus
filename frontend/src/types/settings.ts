export interface LdapSettingsFields {
  enabled: boolean
  server_uri: string
  start_tls: boolean
  verify_cert: boolean
  ca_cert_file: string
  timeout: number
  bind_dn: string
  user_search_base: string
  user_filter: string
  attr_username: string
  attr_first_name: string
  attr_last_name: string
  attr_employee_number: string
  attr_email: string
  attr_job_title: string
  attr_phone: string
  create_users: boolean
}

export type LdapField = keyof LdapSettingsFields | 'bind_password'

export interface LdapSettings extends LdapSettingsFields {
  bind_password_set: boolean
  /** Fields set by LDAP_* environment variables (read-only in the app). */
  locked: LdapField[]
  env_names: Record<LdapField, string>
}

export interface LdapSettingsInput extends LdapSettingsFields {
  /** `null` keeps the stored password, `''` clears it. */
  bind_password: string | null
}

export interface LdapTestResult {
  server: string
  user: Record<string, string> | null
}

/** Switchable modules and features, see the backend's apps/core/features.py. */
export type ModuleKey =
  'consumables' | 'licenses' | 'procurement' | 'calendar' | 'issues' | 'terminal'
export type FeatureKey =
  | 'calendar_warranty'
  | 'calendar_license_expiry'
  | 'calendar_deliveries'
  | 'consumable_quick_pick'
  | 'software_requests'
  | 'attention_motion'
export type FlagKey = ModuleKey | FeatureKey

export interface SiteSettings {
  /** Effective values: a feature is off while a module it needs is off. */
  flags: Record<FlagKey, boolean>
  /** What the administrator switched, before dependencies apply. */
  stored: Record<FlagKey, boolean>
  definitions: { key: FlagKey; kind: 'module' | 'feature'; requires: ModuleKey[] }[]
  rules: Rules
  /** Whether emails can go out at all: switched on, with a server and a sender. */
  mail_enabled: boolean
  /** Directory login is configured and on; forms show LDAP-related fields. */
  ldap_enabled: boolean
  /** Notification kinds and whether they are switched on site-wide, per channel. */
  notifications: {
    key: NotificationKey
    audience: NotificationAudience
    mail: boolean
    app: boolean
  }[]
}

/** Who a notification is for: the person concerned, IT or department approvers. */
export type NotificationAudience = 'employee' | 'it' | 'approver'

/** How a notification reaches someone: by email or in the app (the bell). */
export type NotificationChannel = 'mail' | 'app'

/** Site-wide switches per notification kind and channel. */
export interface NotificationSettings {
  /** Email can actually go out; without it the email switches have no effect. */
  mail_ready: boolean
  mail: Record<NotificationKey, boolean>
  app: Record<NotificationKey, boolean>
}

/** Deadlines and warning periods (days). */
export interface Rules {
  warranty_warning_days: number
  license_warning_days: number
  default_loan_days: number
  /** 0 = no limit */
  max_loan_days: number
  return_reminder_days: number
}

export type NotificationKey =
  | 'approval_requested'
  | 'request_submitted'
  | 'issue_reported'
  | 'issue_answered'
  | 'assigned_to_me'
  | 'license_expiring'
  | 'request_confirmed'
  | 'request_rejected'
  | 'request_cancelled'
  | 'request_ready'
  | 'request_rescheduled'
  | 'request_handed_out'
  | 'request_extended'
  | 'request_returned'
  | 'return_reminder'
  | 'return_overdue'
  | 'issue_message'
  | 'issue_resolved'

export type MailSecurity = 'starttls' | 'ssl' | 'none'

export interface MailSettings {
  enabled: boolean
  host: string
  port: number
  security: MailSecurity
  username: string
  password_set: boolean
  from_email: string
  from_name: string
  app_url: string
}

export interface MailSettingsInput extends Omit<MailSettings, 'password_set'> {
  /** null keeps the stored password, '' removes it. */
  password: string | null
}
