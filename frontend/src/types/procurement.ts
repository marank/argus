import type { Schemas } from '@/api/types'

export const ORDER_STATUSES: Schemas['PurchaseOrderStatus'][] = [
  'draft',
  'ordered',
  'partially_received',
  'received',
  'cancelled',
]
