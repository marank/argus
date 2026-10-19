import type { Id } from '@/types/common'
import type { CatalogCategory, CatalogModel } from '@/types/reservations'

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
  /** Pool size, only known to IT staff. */
  available: number | null
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

/** Sum of the group's own models; null when availability is hidden. */
export function ownAvailable(category: CatalogCategory): number | null {
  if (category.available === null) return null
  return category.models.reduce((sum, m) => sum + (m.available ?? 0), 0)
}
