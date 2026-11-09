import type { Schemas } from '@/api/types'
import type { Id, ListParams, Page } from '@/types/common'
import type { PeriodQuery } from '@/types/requests'

import { http } from './client'

const base = '/requests'

type AssetRequest = Schemas['AssetRequestOut']

export const requestsApi = {
  list: (params: ListParams = {}) => http.get<Page<Schemas['AssetRequestListOut']>>(base, params),
  get: (id: Id) => http.get<AssetRequest>(`${base}/${id}`),
  create: (data: Schemas['AssetRequestIn']) => http.post<AssetRequest>(base, data),
  createDirect: (data: Schemas['DirectRequestIn']) =>
    http.post<AssetRequest>(`${base}/direct`, data),
  quickAssign: (data: Schemas['QuickAssignIn']) => http.post<AssetRequest>(`${base}/quick`, data),
  cancel: (id: Id) => http.post<AssetRequest>(`${base}/${id}/cancel`),
  confirm: (id: Id, data: Schemas['ConfirmIn']) =>
    http.post<AssetRequest>(`${base}/${id}/confirm`, data),
  reject: (id: Id, comment: string) => http.post<AssetRequest>(`${base}/${id}/reject`, { comment }),
  schedule: (id: Id, data: Schemas['ScheduleIn']) =>
    http.post<AssetRequest>(`${base}/${id}/schedule`, data),
  candidates: (itemId: Id, q?: string) =>
    http.get<Schemas['CandidatesOut']>(`${base}/items/${itemId}/candidates`, { q }),
  allocate: (id: Id, data: Schemas['AllocateIn']) =>
    http.post<AssetRequest>(`${base}/${id}/allocations`, data),
  resolveItem: (id: Id, itemId: Id, assetModel: Id) =>
    http.post<AssetRequest>(`${base}/${id}/items/${itemId}/resolve`, { asset_model: assetModel }),
  /** Fills the open items from the pool; with `itemId` only that one. */
  autoAllocate: (id: Id, itemId?: Id) =>
    http.post<Schemas['AutoAllocateOut']>(
      `${base}/${id}/auto-allocate${itemId ? `?item=${itemId}` : ''}`,
    ),
  removeAllocation: (id: Id, allocationId: Id) =>
    http.delete<AssetRequest>(`${base}/${id}/allocations/${allocationId}`),
  markReady: (id: Id, data: Schemas['ReadyIn']) =>
    http.post<AssetRequest>(`${base}/${id}/ready`, data),
  assign: (id: Id, data: Schemas['AssetRequestAssignIn']) =>
    http.post<AssetRequest>(`${base}/${id}/assign`, data),
  extend: (id: Id, endDate: string) =>
    http.post<AssetRequest>(`${base}/${id}/extend`, { end_date: endDate }),
  remind: (id: Id) => http.post<AssetRequest>(`${base}/${id}/remind`),
  reopen: (id: Id) => http.post<AssetRequest>(`${base}/${id}/reopen`),
  handOut: (id: Id, data: Schemas['HandOutIn']) =>
    http.post<AssetRequest>(`${base}/${id}/hand-out`, data),
  returnDevices: (id: Id, data: Partial<Schemas['ReturnIn']> = {}) =>
    http.post<AssetRequest>(`${base}/${id}/return`, data),
  /** Handed out outside the system, without recording the devices. */
  handOutUnrecorded: (id: Id, data: Partial<Schemas['UnrecordedIn']> = {}) =>
    http.post<AssetRequest>(`${base}/${id}/hand-out-unrecorded`, data),
  /** The devices handed out without being recorded are back. */
  returnUnrecorded: (id: Id, data: Partial<Schemas['UnrecordedIn']> = {}) =>
    http.post<AssetRequest>(`${base}/${id}/return-unrecorded`, data),
}

export const portalApi = {
  catalog: (period?: PeriodQuery) =>
    http.get<Schemas['CatalogCategoryOut'][]>('/portal/catalog', period),
  availability: (period: PeriodQuery) =>
    http.get<Schemas['AvailabilityOut']>('/portal/availability', period),
  myAssets: () => http.get<Schemas['MyAssetOut'][]>('/portal/my-assets'),
  myAsset: (id: Id) => http.get<Schemas['MyAssetOut']>(`/portal/my-assets/${id}`),
  myIssues: () => http.get<Schemas['OwnIssueWithDeviceOut'][]>('/portal/my-issues'),
  myIssue: (id: Id) => http.get<Schemas['AssetIssueDetailOut']>(`/portal/my-issues/${id}`),
  myIssueMessage: (id: Id, text: string) =>
    http.post<Schemas['AssetIssueDetailOut']>(`/portal/my-issues/${id}/messages`, { text }),
  /** The reporter marks the problem resolved, optionally saying how. */
  resolveMyIssue: (id: Id, text = '') =>
    http.post<Schemas['AssetIssueDetailOut']>(`/portal/my-issues/${id}/resolve`, { text }),
  myLicenses: () => http.get<Schemas['OwnLicenseOut'][]>('/portal/my-licenses'),
  myConsumables: () => http.get<Schemas['MyConsumablesOut'][]>('/portal/my-consumables'),
  menuCounts: () => http.get<Schemas['MenuCountsOut']>('/portal/menu-counts'),
  reportIssue: (assetId: Id, data: { kind: Schemas['AssetIssueKind']; description: string }) =>
    http.post<Schemas['OwnIssueOut']>(`/portal/my-assets/${assetId}/issues`, data),
}

/** Department approvers decide on requests before IT gets them. */
export const approvalsApi = {
  list: (params: ListParams = {}) =>
    http.get<Page<Schemas['AssetRequestListOut']>>('/approvals', params),
  approve: (id: Id, comment: string) =>
    http.post<AssetRequest>(`/approvals/${id}/approve`, { comment }),
  decline: (id: Id, comment: string) =>
    http.post<AssetRequest>(`/approvals/${id}/decline`, { comment }),
}

export const terminalApi = {
  pickups: (q?: string) => http.get<Schemas['TerminalPickupOut'][]>('/terminal/pickups', { q }),
  get: (id: Id) => http.get<Schemas['TerminalPickupDetailOut']>(`/terminal/pickups/${id}`),
  sign: (id: Id, data: Schemas['TerminalSignIn']) =>
    http.post<Schemas['TerminalPickupDetailOut']>(`/terminal/pickups/${id}/sign`, data),
  people: (q: string) => http.get<Schemas['TerminalPersonOut'][]>('/terminal/people', { q }),
  staff: () => http.get<Schemas['TerminalStaffOut'][]>('/terminal/staff'),
}
