import type {
  AssetModel,
  Category,
  Location,
  Manufacturer,
  NumberSequence,
  Supplier,
} from '@/types/masterdata'

import { http } from './client'
import { createResource } from './resource'

export const manufacturersApi = createResource<Manufacturer>('/masterdata/manufacturers')
export const suppliersApi = createResource<Supplier>('/masterdata/suppliers')
export const categoriesApi = createResource<Category>('/masterdata/categories')
export const locationsApi = createResource<Location>('/masterdata/locations')
export const assetModelsApi = createResource<AssetModel>('/masterdata/models')
export const numberSequencesApi = {
  ...createResource<NumberSequence>('/masterdata/number-sequences'),
  preview: (data: Partial<NumberSequence>) =>
    http.post<{ examples: string[] }>('/masterdata/number-sequences/preview', data),
}
