import type { Id } from '@/types/common'
import { toIsoDate } from '@/composables/useFormat'
import type {
  AvailabilityCounts,
  CatalogCategory,
  CatalogModel,
  Duration,
  PeriodQuery,
} from '@/types/requests'

/** One line of the request being assembled. */
export interface CartLine {
  key: string
  label: string
  category?: Id
  asset_model?: Id
  /** Free text for something not in the catalog. */
  description?: string
  /** Direct hand-out: a specific device (quantity 1) or a consumable stock. */
  asset?: Id
  consumable?: Id
  /** Inventory number of the device, shown in the cart. */
  code?: string
  /** Most units the line can hold (what the stock has free). */
  max?: number
  quantity: number
  note: string
  /** Free in the request period, only known to IT staff. */
  available: number | null
}

/** When the devices are needed; shared by the period card, the cart and the catalog. */
export interface RequestPeriod {
  duration: Duration
  range: [number, number]
  start: number
  /** Preferred pickup day: follows the first day unless the employee picks another. */
  pickup: number
}

/** Availability window: from the pickup day (devices leave then) to the end. */
export function periodQuery(period: RequestPeriod): PeriodQuery {
  const first = period.duration === 'permanent' ? period.start : period.range[0]
  const start = toIsoDate(Math.min(period.pickup, first))!
  if (period.duration === 'permanent') return { start, permanent: true }
  return { start, end: toIsoDate(period.range[1])! }
}

/** Something that can be put into the request: a whole group ("any") or a model. */
export interface CatalogOption {
  key: string
  category: CatalogCategory
  model?: CatalogModel
}

export const optionKey = (category: CatalogCategory, model?: CatalogModel) =>
  model ? `m${model.id}` : `c${category.id}`

/** "Any device of this group" only makes sense when allowed and there is a choice. */
export function offersAnyModel(category: CatalogCategory): boolean {
  return category.allow_any_model && category.models.length > 1
}

/** Counts of an option for display; null when availability is hidden. */
export function optionCounts(
  category: CatalogCategory,
  model?: CatalogModel,
): AvailabilityCounts | null {
  const source = model ?? category
  if (source.available === null || source.reserved === null) return null
  return { available: source.available, reserved: source.reserved }
}
