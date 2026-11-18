import type { RouteLocationRaw } from 'vue-router'

import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'

export type Activity = Schemas['ActivityOut']
export type ActivityArea = Schemas['ActivityArea']
export type ActivityKind = Schemas['ActivityKind']

export const ACTIVITY_AREAS = allValues<ActivityArea>({
  requests: true,
  assets: true,
  consumables: true,
  licenses: true,
  issues: true,
  procurement: true,
})

export const ACTIVITY_KINDS = allValues<ActivityKind>({
  request_created: true,
  request_direct: true,
  request_quick: true,
  request_approved: true,
  request_declined: true,
  request_confirmed: true,
  request_rejected: true,
  request_cancelled: true,
  request_assigned: true,
  request_allocated: true,
  request_ready: true,
  request_reopened: true,
  request_rescheduled: true,
  request_handed_out: true,
  request_returned: true,
  request_extended: true,
  request_reminded: true,
  request_completed: true,
  asset_created: true,
  assets_created: true,
  assets_imported: true,
  asset_status_changed: true,
  asset_assigned: true,
  asset_returned: true,
  asset_replaced: true,
  asset_component_replaced: true,
  asset_repair: true,
  asset_maintenance: true,
  asset_inspection: true,
  asset_note: true,
  asset_deleted: true,
  issue_reported: true,
  issue_in_progress: true,
  issue_reopened: true,
  issue_resolved: true,
  consumable_receipt: true,
  consumable_issue: true,
  consumable_return: true,
  consumable_adjustment: true,
  consumable_consumption: true,
  license_created: true,
  license_deleted: true,
  license_assigned: true,
  license_unassigned: true,
  order_created: true,
  order_placed: true,
  order_received: true,
  order_cancelled: true,
  order_deleted: true,
})

/** The page of the object a row is about; none when it was deleted or covers several devices. */
export function activityTarget(row: Activity): RouteLocationRaw | null {
  if (row.area === 'consumables') return { name: 'consumables' }
  if (!row.subject_id) return null
  const id = row.subject_id
  switch (row.area) {
    case 'requests':
      return { name: 'request', params: { id } }
    case 'assets':
      return { name: 'asset', params: { id } }
    case 'licenses':
      return { name: 'license', params: { id } }
    case 'issues':
      return { name: 'issue', params: { id } }
    case 'procurement':
      return { name: 'order', params: { id } }
  }
}
