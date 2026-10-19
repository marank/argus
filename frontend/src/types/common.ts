/** Primary keys are UUIDs, serialized as strings. */
export type Id = string

export interface Page<T> {
  items: T[]
  count: number
}

export interface Ref {
  id: Id
  name: string
}

export interface ListParams {
  page?: number
  page_size?: number
  q?: string
  ordering?: string
  [filter: string]: string | number | boolean | null | undefined | (string | number)[]
}
