import { i18n } from '@/i18n'
import type { ReservationItem } from '@/types/reservations'

/** "Any headset" for category requests, otherwise the model name. */
export function itemLabel(
  item: Pick<ReservationItem, 'label' | 'category' | 'asset_model' | 'description'>,
): string {
  // Model lines and free text ("Laptops: 64 GB RAM") already carry a readable label.
  if (item.asset_model || !item.category || item.description) return item.label
  return i18n.global.t('reservations.new.any', { category: item.category.name })
}
