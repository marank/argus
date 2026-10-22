import type { Id, ListParams, Page } from '@/types/common'
import type {
  AssetIssueDetail,
  IssueKind,
  OwnIssue,
  OwnIssueWithDevice,
  OwnLicense,
} from '@/types/inventory'
import type {
  Candidates,
  CatalogCategory,
  DirectRequestInput,
  QuickAssignInput,
  MyAsset,
  MyConsumables,
  PeriodAvailability,
  PeriodQuery,
  Reservation,
  ReservationInput,
  ReservationListItem,
  HandOutInput,
  HandoverMode,
  MenuCounts,
  ReturnInput,
  SignInput,
  TerminalPerson,
  TerminalPickup,
  TerminalPickupDetail,
  TerminalStaff,
} from '@/types/reservations'

import { http } from './client'

const base = '/reservations'

export interface ConfirmInput {
  items: { id: Id; quantity_confirmed: number }[]
  comment: string
}

export const reservationsApi = {
  list: (params: ListParams = {}) => http.get<Page<ReservationListItem>>(base, params),
  get: (id: Id) => http.get<Reservation>(`${base}/${id}`),
  create: (data: ReservationInput) => http.post<Reservation>(base, data),
  createDirect: (data: DirectRequestInput) => http.post<Reservation>(`${base}/direct`, data),
  quickAssign: (data: QuickAssignInput) => http.post<Reservation>(`${base}/quick`, data),
  cancel: (id: Id) => http.post<Reservation>(`${base}/${id}/cancel`),
  confirm: (id: Id, data: ConfirmInput) => http.post<Reservation>(`${base}/${id}/confirm`, data),
  reject: (id: Id, comment: string) => http.post<Reservation>(`${base}/${id}/reject`, { comment }),
  schedule: (
    id: Id,
    data: {
      pickup_at: string | null
      pickup_location: Id | null
      handover_mode?: HandoverMode
      /** Tell the employee about the change; left out, they are told. */
      notify?: boolean
    },
  ) => http.post<Reservation>(`${base}/${id}/schedule`, data),
  candidates: (itemId: Id, q?: string) =>
    http.get<Candidates>(`${base}/items/${itemId}/candidates`, { q }),
  allocate: (
    id: Id,
    data: {
      item: Id
      asset?: Id
      consumable?: Id
      license?: Id
      quantity?: number
      code?: string
    },
  ) => http.post<Reservation>(`${base}/${id}/allocations`, data),
  resolveItem: (id: Id, itemId: Id, assetModel: Id) =>
    http.post<Reservation>(`${base}/${id}/items/${itemId}/resolve`, { asset_model: assetModel }),
  autoAllocate: (id: Id) =>
    http.post<{ allocated: number; reservation: Reservation }>(`${base}/${id}/auto-allocate`),
  removeAllocation: (id: Id, allocationId: Id) =>
    http.delete<Reservation>(`${base}/${id}/allocations/${allocationId}`),
  markReady: (
    id: Id,
    data: {
      handover_mode: HandoverMode
      skip_device_check: boolean
      pickup_at: string | null
      pickup_location: Id | null
      /** Send the employee the ready message; left out, it is sent. */
      notify?: boolean
    },
  ) => http.post<Reservation>(`${base}/${id}/ready`, data),
  assign: (id: Id, data: { team: Id | null; assignee: Id | null }) =>
    http.post<Reservation>(`${base}/${id}/assign`, data),
  extend: (id: Id, endDate: string) =>
    http.post<Reservation>(`${base}/${id}/extend`, { end_date: endDate }),
  remind: (id: Id) => http.post<Reservation>(`${base}/${id}/remind`),
  reopen: (id: Id) => http.post<Reservation>(`${base}/${id}/reopen`),
  handOut: (id: Id, data: HandOutInput) => http.post<Reservation>(`${base}/${id}/hand-out`, data),
  returnDevices: (id: Id, data: Partial<ReturnInput> = {}) =>
    http.post<Reservation>(`${base}/${id}/return`, data),
}

export const portalApi = {
  catalog: (period?: PeriodQuery) => http.get<CatalogCategory[]>('/portal/catalog', period),
  availability: (period: PeriodQuery) =>
    http.get<PeriodAvailability>('/portal/availability', period),
  myAssets: () => http.get<MyAsset[]>('/portal/my-assets'),
  myAsset: (id: Id) => http.get<MyAsset>(`/portal/my-assets/${id}`),
  myIssues: () => http.get<OwnIssueWithDevice[]>('/portal/my-issues'),
  myIssue: (id: Id) => http.get<AssetIssueDetail>(`/portal/my-issues/${id}`),
  myIssueMessage: (id: Id, text: string) =>
    http.post<AssetIssueDetail>(`/portal/my-issues/${id}/messages`, { text }),
  /** The reporter marks the problem resolved, optionally saying how. */
  resolveMyIssue: (id: Id, text = '') =>
    http.post<AssetIssueDetail>(`/portal/my-issues/${id}/resolve`, { text }),
  myLicenses: () => http.get<OwnLicense[]>('/portal/my-licenses'),
  myConsumables: () => http.get<MyConsumables[]>('/portal/my-consumables'),
  menuCounts: () => http.get<MenuCounts>('/portal/menu-counts'),
  reportIssue: (assetId: Id, data: { kind: IssueKind; description: string }) =>
    http.post<OwnIssue>(`/portal/my-assets/${assetId}/issues`, data),
}

/** Department approvers decide on requests before IT gets them. */
export const approvalsApi = {
  list: (params: ListParams = {}) => http.get<Page<ReservationListItem>>('/approvals', params),
  approve: (id: Id, comment: string) =>
    http.post<Reservation>(`/approvals/${id}/approve`, { comment }),
  decline: (id: Id, comment: string) =>
    http.post<Reservation>(`/approvals/${id}/decline`, { comment }),
}

export const terminalApi = {
  pickups: (q?: string) => http.get<TerminalPickup[]>('/terminal/pickups', { q }),
  get: (id: Id) => http.get<TerminalPickupDetail>(`/terminal/pickups/${id}`),
  sign: (id: Id, data: SignInput) =>
    http.post<TerminalPickupDetail>(`/terminal/pickups/${id}/sign`, data),
  people: (q: string) => http.get<TerminalPerson[]>('/terminal/people', { q }),
  staff: () => http.get<TerminalStaff[]>('/terminal/staff'),
}
