import type { Schemas } from '@/api/types'
import type { Id } from '@/types/common'
import { toIsoDate } from '@/composables/useFormat'
import type { PeriodQuery } from '@/types/requests'

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
  duration: Schemas['Duration']
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

/** What the request is for and who it is for (null: the person signed in), plus a message to IT. */
export interface RequestDetails {
  title: string
  notes: string
  requester: Id | null
}

/** The request to send, from its period, details and the lines in the cart. */
export function requestInput(
  period: RequestPeriod,
  details: RequestDetails,
  lines: CartLine[],
): Schemas['AssetRequestIn'] {
  const first = period.duration === 'permanent' ? period.start : period.range[0]
  return {
    title: details.title,
    notes: details.notes,
    duration: period.duration,
    start_date: toIsoDate(first)!,
    end_date: periodQuery(period).end ?? null,
    requested_pickup_date: toIsoDate(period.pickup),
    requester: details.requester,
    items: lines.map(({ category, asset_model, description, quantity, note }) => ({
      category: category ?? null,
      asset_model: asset_model ?? null,
      description: description ?? '',
      quantity,
      note,
    })),
  }
}

/** Something that can be put into the request: a whole group ("any") or a model. */
export interface CatalogOption {
  key: string
  category: Schemas['CatalogCategoryOut']
  model?: Schemas['CatalogModelOut']
}

export const optionKey = (
  category: Schemas['CatalogCategoryOut'],
  model?: Schemas['CatalogModelOut'],
) => (model ? `m${model.id}` : `c${category.id}`)

/** "Any device of this group" only makes sense when allowed and there is a choice. */
export function offersAnyModel(category: Schemas['CatalogCategoryOut']): boolean {
  return category.allow_any_model && category.models.length > 1
}

/** Counts of an option for display; null when availability is hidden. */
export function optionCounts(
  category: Schemas['CatalogCategoryOut'],
  model?: Schemas['CatalogModelOut'],
): Schemas['CountsOut'] | null {
  const source = model ?? category
  if (source.available === null || source.reserved === null) return null
  return { available: source.available, reserved: source.reserved }
}

/** One of the employee's devices with the catalog entries that fit it (e.g. its ink). */
export interface FittingDevice {
  asset: Schemas['MyConsumablesOut']['asset']
  options: { category: Schemas['CatalogCategoryOut']; model: Schemas['CatalogModelOut'] }[]
}

/** What fits the employee's devices, limited to what the catalog offers; devices without any left out. */
export function fittingDevices(
  groups: Schemas['MyConsumablesOut'][],
  catalog: Schemas['CatalogCategoryOut'][],
): FittingDevice[] {
  const byId = new Map<Id, FittingDevice['options'][number]>()
  for (const category of catalog) {
    for (const model of category.models) byId.set(model.id, { category, model })
  }
  return groups
    .map((group) => ({
      asset: group.asset,
      options: group.consumables.flatMap((c) => byId.get(c.id) ?? []),
    }))
    .filter((device) => device.options.length)
}
