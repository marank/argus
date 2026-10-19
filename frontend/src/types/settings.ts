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
