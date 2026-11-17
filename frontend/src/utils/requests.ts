import { locationsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import { i18n } from '@/i18n'

/** "Laptop · any model": the singular item name, falling back to the category name. */
export function anyModelLabel(category: { name: string; item_name?: string }): string {
  return i18n.global.t('requests.new.any', { item: category.item_name || category.name })
}

/** "Laptop · any model" for category requests, otherwise the model name. */
export function itemLabel(
  item: Pick<Schemas['AssetRequestItemOut'], 'label' | 'category' | 'asset_model' | 'description'>,
): string {
  // Model lines and free text ("Laptops: 64 GB RAM") already carry a readable label.
  if (item.asset_model || !item.category || item.description) return item.label
  return anyModelLabel(item.category)
}

/** Model name of what was allocated: device, consumable or license seat. */
export function allocationModel(
  allocation: Pick<Schemas['AllocationOut'], 'asset' | 'consumable' | 'license'>,
): string {
  return (
    allocation.asset?.model.full_name ??
    allocation.consumable?.model.full_name ??
    allocation.license?.model.full_name ??
    ''
  )
}

/** Short code of an allocation: inventory number, quantity or the device a seat is on. */
export function allocationCode(
  allocation: Pick<Schemas['AllocationOut'], 'asset' | 'license' | 'quantity'>,
): string {
  if (allocation.asset) return allocation.asset.inventory_number
  if (allocation.license) return allocation.license.device?.inventory_number ?? ''
  return `${allocation.quantity}×`
}

/** Devices and license seats come back; consumables are used up. */
export function isReturnable(allocation: Schemas['AllocationOut']): boolean {
  return Boolean(allocation.asset || allocation.license)
}

/**
 * Whether a planned pickup (date and time) has passed, or for a plain day ("2026-10-20")
 * whether that day is over.
 */
export function isPast(when: string | null | undefined, now = new Date()): boolean {
  if (!when) return false
  if (when.length === 10) {
    return new Date(`${when}T00:00:00`).getTime() < new Date(now).setHours(0, 0, 0, 0)
  }
  return new Date(when).getTime() < now.getTime()
}

/**
 * Whether IT has planned how the devices reach the employee, which happens when marking
 * it ready (or changing the handover after that). Before that the handover mode is only
 * the default. Older requests got date and place when they were confirmed.
 */
export function handoverPlanned(
  assetRequest: Pick<Schemas['AssetRequestOut'], 'events' | 'pickup_at'>,
): boolean {
  return (
    !!assetRequest.pickup_at ||
    assetRequest.events.some((event) => ['rescheduled', 'ready'].includes(event.kind))
  )
}

/** Proposed handover time: the next full hour from now. */
export function nextFullHour(now = new Date()): number {
  const next = new Date(now)
  next.setHours(now.getHours() + 1, 0, 0, 0)
  return next.getTime()
}

/** The pickup point if there is only one, so the dialogs can fill it in. */
export async function onlyPickupPoint(): Promise<Schemas['LocationOut'] | null> {
  const page = await locationsApi.list({ is_pickup_point: true, page_size: 2 })
  return page.items.length === 1 ? page.items[0]! : null
}
