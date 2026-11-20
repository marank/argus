import { locationsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'

/** The pickup point if there is only one, so the dialogs can fill it in. */
export async function onlyPickupPoint(): Promise<Schemas['LocationOut'] | null> {
  const page = await locationsApi.list({ is_pickup_point: true, page_size: 2 })
  return page.items.length === 1 ? page.items[0]! : null
}
