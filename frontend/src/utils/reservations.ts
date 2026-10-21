import { i18n } from '@/i18n'
import type { Allocation, ReservationItem } from '@/types/reservations'

/** "Laptop · any model": the singular item name, falling back to the category name. */
export function anyModelLabel(category: { name: string; item_name?: string }): string {
  return i18n.global.t('reservations.new.any', { item: category.item_name || category.name })
}

/** "Laptop · any model" for category requests, otherwise the model name. */
export function itemLabel(
  item: Pick<ReservationItem, 'label' | 'category' | 'asset_model' | 'description'>,
): string {
  // Model lines and free text ("Laptops: 64 GB RAM") already carry a readable label.
  if (item.asset_model || !item.category || item.description) return item.label
  return anyModelLabel(item.category)
}

/** Model name of what was allocated: device, consumable or license seat. */
export function allocationModel(
  allocation: Pick<Allocation, 'asset' | 'consumable' | 'license'>,
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
  allocation: Pick<Allocation, 'asset' | 'license' | 'quantity'>,
): string {
  if (allocation.asset) return allocation.asset.inventory_number
  if (allocation.license) return allocation.license.device?.inventory_number ?? ''
  return `${allocation.quantity}×`
}

/** Devices and license seats come back; consumables are used up. */
export function isReturnable(allocation: Allocation): boolean {
  return Boolean(allocation.asset || allocation.license)
}
