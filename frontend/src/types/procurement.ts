import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'

export const ORDER_STATUSES = allValues<Schemas['PurchaseOrderStatus']>({
  draft: true,
  ordered: true,
  partially_received: true,
  received: true,
  cancelled: true,
})
