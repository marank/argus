import type { Schemas } from '@/api/types'

export const ASSET_REQUEST_STATUSES: Schemas['AssetRequestStatus'][] = [
  'pending_approval',
  'submitted',
  'confirmed',
  'ready',
  'handed_out',
  'completed',
  'rejected',
  'cancelled',
]

/** The period of a request; availability in the catalog refers to it. */
export type PeriodQuery = {
  start: string
  end?: string
  permanent?: boolean
}
