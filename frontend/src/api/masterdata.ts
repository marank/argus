import type { Schemas } from '@/api/types'
import type { Id } from '@/types/common'

import { http } from './client'
import { createResource } from './resource'

export const manufacturersApi = createResource<Schemas['ManufacturerOut']>(
  '/masterdata/manufacturers',
)
export const suppliersApi = createResource<Schemas['SupplierOut']>('/masterdata/suppliers')
export const categoriesApi = createResource<Schemas['CategoryOut']>('/masterdata/categories')
export const componentTypesApi = createResource<Schemas['ComponentTypeOut']>(
  '/masterdata/component-types',
)
export const locationsApi = createResource<Schemas['LocationOut']>('/masterdata/locations')
export const assetModelsApi = createResource<Schemas['AssetModelOut']>('/masterdata/models')
export const numberSequencesApi = {
  ...createResource<Schemas['NumberSequenceOut']>('/masterdata/number-sequences'),
  preview: (data: Partial<Schemas['NumberSequenceOut']>) =>
    http.post<{ examples: string[] }>('/masterdata/number-sequences/preview', data),
}

/**
 * The tracked parts devices of a category have, e.g. the battery. Without them the forms
 * still work (the parts just do not show), so a failed request leaves the list empty.
 */
export async function loadComponentTypes(
  category: Id | null | undefined,
): Promise<Schemas['ComponentTypeOut'][]> {
  if (!category) return []
  try {
    return (await componentTypesApi.list({ category, page_size: 50 })).items
  } catch {
    return []
  }
}
