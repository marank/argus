import type { Id, ListParams, Page } from '@/types/common'
import type {
  Asset,
  AssetDetail,
  AssetEvent,
  AssetEventWithAsset,
  AssetInput,
  LookupResult,
  StockItem,
  StockMovement,
  StockReason,
} from '@/types/inventory'

import { http } from './client'

export const assetsApi = {
  list: (params: ListParams = {}) => http.get<Page<Asset>>('/inventory/assets', params),
  get: (id: Id) => http.get<AssetDetail>(`/inventory/assets/${id}`),
  create: (data: AssetInput) => http.post<AssetDetail>('/inventory/assets', data),
  bulkCreate: (data: Partial<AssetInput> & { serial_numbers: string[] }) =>
    http.post<Asset[]>('/inventory/assets/bulk', data),
  update: (id: Id, data: AssetInput) => http.put<AssetDetail>(`/inventory/assets/${id}`, data),
  assign: (id: Id, user: Id | null) =>
    http.post<AssetDetail>(`/inventory/assets/${id}/assign`, { user }),
  remove: (id: Id) => http.delete(`/inventory/assets/${id}`),
  events: (id: Id) => http.get<AssetEvent[]>(`/inventory/assets/${id}/events`),
  addEvent: (id: Id, data: Record<string, unknown>) =>
    http.post<AssetEvent>(`/inventory/assets/${id}/events`, data),
}

export const eventsApi = {
  list: (params: ListParams = {}) =>
    http.get<Page<AssetEventWithAsset>>('/inventory/events', params),
  remove: (id: Id) => http.delete(`/inventory/events/${id}`),
}

export const stockApi = {
  list: (params: ListParams = {}) => http.get<Page<StockItem>>('/inventory/stock', params),
  get: (id: Id) => http.get<StockItem>(`/inventory/stock/${id}`),
  create: (data: { model: Id; location: Id; min_quantity: number }) =>
    http.post<StockItem>('/inventory/stock', data),
  update: (id: Id, data: { min_quantity: number }) =>
    http.put<StockItem>(`/inventory/stock/${id}`, data),
  movements: (id: Id) => http.get<StockMovement[]>(`/inventory/stock/${id}/movements`),
  move: (
    id: Id,
    data: { delta: number; reason: StockReason; note?: string; recipient?: Id | null },
  ) => http.post<StockItem>(`/inventory/stock/${id}/move`, data),
}

export const lookupApi = {
  lookup: (code: string) => http.get<LookupResult>('/inventory/lookup', { code }),
}
