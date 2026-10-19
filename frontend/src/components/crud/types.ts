import type { Component, VNodeChild } from 'vue'

import type { Id, ListParams, Page } from '@/types/common'

/* eslint-disable @typescript-eslint/no-explicit-any */

interface BaseField {
  key: string
  /** i18n key of the label. */
  label: string
  required?: boolean
  /** Grid span out of 2 columns. */
  span?: 1 | 2
  help?: string
}

export type FieldDef = BaseField &
  (
    | { type: 'text' | 'textarea' | 'mono' }
    | { type: 'number'; min?: number; max?: number; precision?: number }
    | { type: 'switch' }
    | { type: 'enum'; group: string; values: string[] }
    | { type: 'icon' }
    | {
        type: 'entity'
        fetcher: (params: ListParams) => Promise<Page<any>>
        display: (item: any) => string
        params?: ListParams
        multiple?: boolean
        /** The currently selected related record(s) of a row, for the label. */
        initial?: (row: any) => any
      }
  )

/** A titled group of fields in the edit drawer. */
export interface FormSection {
  /** i18n key of the section title; omit for the first, untitled block. */
  title?: string
  fields: FieldDef[]
  /** Optional component rendered below the fields; receives the live `form`. */
  extra?: Component
}

export interface ColumnDef<T> {
  key: string
  label: string
  /** Backend ordering field; enables sorting. */
  sorter?: string
  width?: number
  render?: (row: T) => VNodeChild
}

export interface FilterDef {
  key: string
  label: string
  type: 'boolean' | 'enum' | 'entity'
  group?: string
  values?: string[]
  fetcher?: (params: ListParams) => Promise<Page<any>>
  display?: (item: any) => string
}

export interface ResourceDef<T extends { id: Id }> {
  /** i18n key suffix under masterdata.resources / masterdata.singular. */
  key: string
  api: {
    list: (params: ListParams) => Promise<Page<T>>
    create: (data: any) => Promise<T>
    update: (id: Id, data: any) => Promise<T>
    remove: (id: Id) => Promise<void>
  }
  ordering?: string
  columns: ColumnDef<T>[]
  sections: FormSection[]
  filters?: FilterDef[]
  defaults: () => Record<string, unknown>
  /** Convert a row from the API into form values. */
  toForm: (row: T) => Record<string, unknown>
  /** Primary label of a record, used in titles and confirmations. */
  title: (row: T) => string
}

export function sectionFields(resource: ResourceDef<any>): FieldDef[] {
  return resource.sections.flatMap((section) => section.fields)
}

export function defineResource<T extends { id: Id }>(def: ResourceDef<T>): ResourceDef<T> {
  return def
}
