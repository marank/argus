import type { Schemas } from '@/api/types'

import { http } from './client'
import { createResource } from './resource'

export const manufacturersApi = createResource<Schemas['ManufacturerOut']>(
  '/masterdata/manufacturers',
)
export const suppliersApi = createResource<Schemas['SupplierOut']>('/masterdata/suppliers')
export const categoriesApi = createResource<Schemas['CategoryOut']>('/masterdata/categories')
export const locationsApi = createResource<Schemas['LocationOut']>('/masterdata/locations')
export const assetModelsApi = createResource<Schemas['AssetModelOut']>('/masterdata/models')
export const numberSequencesApi = {
  ...createResource<Schemas['NumberSequenceOut']>('/masterdata/number-sequences'),
  preview: (data: Partial<Schemas['NumberSequenceOut']>) =>
    http.post<{ examples: string[] }>('/masterdata/number-sequences/preview', data),
}
