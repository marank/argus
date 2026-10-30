import type { Schemas } from '@/api/types'
import type { Id, ListParams, Page } from '@/types/common'

import { http } from './client'

type Asset = Schemas['AssetOut']
type AssetDetail = Schemas['AssetDetailOut']
type Consumable = Schemas['ConsumableOut']
type LicenseDetail = Schemas['LicenseDetailOut']
type AssetIssueDetail = Schemas['AssetIssueDetailOut']

export const assetsApi = {
  list: (params: ListParams = {}) => http.get<Page<Asset>>('/inventory/assets', params),
  get: (id: Id) => http.get<AssetDetail>(`/inventory/assets/${id}`),
  create: (data: Schemas['AssetIn']) => http.post<AssetDetail>('/inventory/assets', data),
  bulkCreate: (data: Schemas['AssetBulkIn']) => http.post<Asset[]>('/inventory/assets/bulk', data),
  seriesPreview: (model: Id, count: number) =>
    http.get<Schemas['AssetSeriesPreviewOut']>('/inventory/assets/series/preview', {
      model,
      count,
    }),
  createSeries: (data: Schemas['AssetSeriesIn']) =>
    http.post<Asset[]>('/inventory/assets/series', data),
  update: (id: Id, data: Schemas['AssetIn']) =>
    http.put<AssetDetail>(`/inventory/assets/${id}`, data),
  assign: (id: Id, user: Schemas['AssetAssignIn']['user']) =>
    http.post<AssetDetail>(`/inventory/assets/${id}/assign`, { user }),
  remove: (id: Id) => http.remove(`/inventory/assets/${id}`),
  events: (id: Id) => http.get<Schemas['AssetEventOut'][]>(`/inventory/assets/${id}/events`),
  addEvent: (id: Id, data: Schemas['AssetEventIn']) =>
    http.post<Schemas['AssetEventOut']>(`/inventory/assets/${id}/events`, data),
}

export const eventsApi = {
  list: (params: ListParams = {}) =>
    http.get<Page<Schemas['AssetEventWithAssetOut']>>('/inventory/events', params),
  remove: (id: Id) => http.remove(`/inventory/events/${id}`),
}

export const consumablesApi = {
  list: (params: ListParams = {}) => http.get<Page<Consumable>>('/inventory/consumables', params),
  get: (id: Id) => http.get<Consumable>(`/inventory/consumables/${id}`),
  create: (data: Schemas['ConsumableIn']) => http.post<Consumable>('/inventory/consumables', data),
  update: (id: Id, data: Schemas['ConsumableUpdateIn']) =>
    http.put<Consumable>(`/inventory/consumables/${id}`, data),
  movements: (id: Id) =>
    http.get<Schemas['ConsumableMovementOut'][]>(`/inventory/consumables/${id}/movements`),
  move: (id: Id, data: Schemas['ConsumableMoveIn']) =>
    http.post<Consumable>(`/inventory/consumables/${id}/move`, data),
}

export const licensesApi = {
  list: (params: ListParams = {}) =>
    http.get<Page<Schemas['LicenseOut']>>('/inventory/licenses', params),
  get: (id: Id) => http.get<LicenseDetail>(`/inventory/licenses/${id}`),
  create: (data: Schemas['LicenseIn']) => http.post<LicenseDetail>('/inventory/licenses', data),
  update: (id: Id, data: Schemas['LicenseIn']) =>
    http.put<LicenseDetail>(`/inventory/licenses/${id}`, data),
  remove: (id: Id) => http.remove(`/inventory/licenses/${id}`),
  assign: (id: Id, data: Schemas['LicenseAssignIn']) =>
    http.post<LicenseDetail>(`/inventory/licenses/${id}/assignments`, data),
  unassign: (id: Id, assignmentId: Id) =>
    http.delete<LicenseDetail>(`/inventory/licenses/${id}/assignments/${assignmentId}`),
}

export const issuesApi = {
  list: (params: ListParams = {}) =>
    http.get<Page<Schemas['AssetIssueOut']>>('/inventory/issues', params),
  get: (id: Id) => http.get<AssetIssueDetail>(`/inventory/issues/${id}`),
  /** Change the status, optionally with a message sent along. */
  update: (id: Id, data: Schemas['AssetIssueUpdateIn']) =>
    http.put<AssetIssueDetail>(`/inventory/issues/${id}`, data),
  message: (id: Id, text: Schemas['IssueMessageIn']['text']) =>
    http.post<AssetIssueDetail>(`/inventory/issues/${id}/messages`, { text }),
  assign: (id: Id, data: Schemas['IssueAssignIn']) =>
    http.post<AssetIssueDetail>(`/inventory/issues/${id}/assign`, data),
}

export const lookupApi = {
  lookup: (code: string) => http.get<Schemas['LookupOut']>('/inventory/lookup', { code }),
}
