import type { Id } from '@/types/common'
import { toIsoDate } from '@/composables/useFormat'
import type {
  AvailabilityCounts,
  CatalogCategory,
  CatalogModel,
  Duration,
  PeriodQuery,
} from '@/types/reservations'

/** One line of the request being assembled. */
export interface CartLine {
  key: string
  label: string
  category?: Id
  asset_model?: Id
  /** Free text for something not in the catalog. */
  description?: string
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
}

export function periodQuery(period: RequestPeriod): PeriodQuery {
  if (period.duration === 'permanent') return { start: toIsoDate(period.start)!, permanent: true }
  return { start: toIsoDate(period.range[0])!, end: toIsoDate(period.range[1])! }
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
