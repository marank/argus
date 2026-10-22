import type { Id, ListParams, Page } from '@/types/common'

import { http } from './client'

/** Standard list/get/create/update/delete endpoints of a REST resource. */
export function createResource<T, TInput = Partial<T>>(path: string) {
  return {
    path,
    list: (params: ListParams = {}) => http.get<Page<T>>(path, params),
    get: (id: Id) => http.get<T>(`${path}/${id}`),
    create: (data: TInput) => http.post<T>(path, data),
    update: (id: Id, data: TInput) => http.put<T>(`${path}/${id}`, data),
    remove: (id: Id) => http.remove(`${path}/${id}`),
  }
}

export type Resource<T, TInput = Partial<T>> = ReturnType<typeof createResource<T, TInput>>
