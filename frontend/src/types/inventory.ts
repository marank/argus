import type { Schemas } from '@/api/types'

export const ASSET_STATUSES: Schemas['AssetStatus'][] = [
  'in_stock',
  'reserved',
  'in_use',
  'in_repair',
  'lost',
  'retired',
]
export const ASSET_CONDITIONS: Schemas['Condition'][] = ['new', 'good', 'worn', 'defective']

/** Kinds a technician records by hand; the others are written by workflows. */
export const MANUAL_EVENT_KINDS: Schemas['AssetEventKind'][] = [
  'battery_replaced',
  'component_replaced',
  'repair',
  'maintenance',
  'inspection',
  'note',
]

export const ISSUE_KINDS: Schemas['AssetIssueKind'][] = ['defect', 'damage', 'lost', 'other']
