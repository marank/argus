import { i18n } from '@/i18n'
import type { ReservationItem } from '@/types/reservations'

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
