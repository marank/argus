import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'

export const ASSET_REQUEST_STATUSES = allValues<Schemas['AssetRequestStatus']>({
  pending_approval: true,
  submitted: true,
  confirmed: true,
  ready: true,
  handed_out: true,
  completed: true,
  rejected: true,
  cancelled: true,
})

/** The period of a request; availability in the catalog refers to it. */
export type PeriodQuery = {
  start: string
  end?: string
  permanent?: boolean
}
