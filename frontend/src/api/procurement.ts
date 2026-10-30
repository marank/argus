import type { Schemas } from '@/api/types'
import type { Id, ListParams, Page } from '@/types/common'

import { http } from './client'

const base = '/procurement/orders'

export interface ReceiptInput {
  line: Id
  quantity: number
  serial_numbers: string[]
  location: Id | null
}

export const ordersApi = {
  list: (params: ListParams = {}) => http.get<Page<Schemas['PurchaseOrderListOut']>>(base, params),
  get: (id: Id) => http.get<Schemas['PurchaseOrderOut']>(`${base}/${id}`),
  create: (data: Schemas['PurchaseOrderIn']) => http.post<Schemas['PurchaseOrderOut']>(base, data),
  update: (id: Id, data: Schemas['PurchaseOrderIn']) =>
    http.put<Schemas['PurchaseOrderOut']>(`${base}/${id}`, data),
  remove: (id: Id) => http.remove(`${base}/${id}`),
  markOrdered: (
    id: Id,
    data: { order_date: string | null; expected_date: string | null; supplier_reference: string },
  ) => http.post<Schemas['PurchaseOrderOut']>(`${base}/${id}/ordered`, data),
  receive: (id: Id, receipts: ReceiptInput[]) =>
    http.post<Schemas['PurchaseOrderOut']>(`${base}/${id}/receive`, { receipts }),
  cancel: (id: Id) => http.post<Schemas['PurchaseOrderOut']>(`${base}/${id}/cancel`),
}

export const needsApi = {
  list: () => http.get<Schemas['NeedsOut']>('/procurement/needs'),
}
