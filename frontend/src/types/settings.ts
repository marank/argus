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

/** Who a notification is for: the person concerned, IT or department approvers. */
export type NotificationAudience = 'employee' | 'it' | 'approver'

/** How a notification reaches someone: by email or in the app (the bell). */
export type NotificationChannel = 'mail' | 'app'
