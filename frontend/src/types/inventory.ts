import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'

export const ASSET_STATUSES = allValues<Schemas['AssetStatus']>({
  in_stock: true,
  reserved: true,
  in_use: true,
  in_repair: true,
  lost: true,
  retired: true,
})
export const ASSET_CONDITIONS = allValues<Schemas['Condition']>({
  new: true,
  good: true,
  worn: true,
  defective: true,
})

/** Kinds a technician records by hand; the others are written by workflows. */
export const MANUAL_EVENT_KINDS: Schemas['AssetEventKind'][] = [
  'component_replaced',
  'repair',
  'maintenance',
  'inspection',
  'note',
]

export const ISSUE_KINDS = allValues<Schemas['AssetIssueKind']>({
  defect: true,
  damage: true,
  lost: true,
  other: true,
})
