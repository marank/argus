import type { Id, ListParams, Page } from '@/types/common'
import type { Needs, Order, OrderInput, OrderListItem } from '@/types/procurement'

import { http } from './client'

const base = '/procurement/orders'

export interface ReceiptInput {
  line: Id
  quantity: number
  serial_numbers: string[]
  location: Id | null
}

export const ordersApi = {
  list: (params: ListParams = {}) => http.get<Page<OrderListItem>>(base, params),
  get: (id: Id) => http.get<Order>(`${base}/${id}`),
  create: (data: OrderInput) => http.post<Order>(base, data),
  update: (id: Id, data: OrderInput) => http.put<Order>(`${base}/${id}`, data),
  remove: (id: Id) => http.remove(`${base}/${id}`),
  markOrdered: (
    id: Id,
    data: { order_date: string | null; expected_date: string | null; supplier_reference: string },
  ) => http.post<Order>(`${base}/${id}/ordered`, data),
  receive: (id: Id, receipts: ReceiptInput[]) =>
    http.post<Order>(`${base}/${id}/receive`, { receipts }),
  cancel: (id: Id) => http.post<Order>(`${base}/${id}/cancel`),
}

export const needsApi = {
  list: () => http.get<Needs>('/procurement/needs'),
}
