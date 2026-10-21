import type { Component, VNodeChild } from 'vue'

import type { PermissionKey } from '@/types/accounts'
import type { Id, ListParams, Page } from '@/types/common'

/* eslint-disable @typescript-eslint/no-explicit-any */

interface BaseField {
  key: string
  /** i18n key of the label. */
  label: string
  required?: boolean
  /** Grid span out of 2 columns. */
  span?: 1 | 2
  /** i18n key of an explanation, or a function returning one (undefined = none). */
  help?: string | (() => string | undefined)
  /** Show the field only while this returns true (e.g. LDAP fields while LDAP is on); gets the live form. */
  visible?: (form: Record<string, any>) => boolean
  /** Read-only for existing records where this returns true; gets the edited row. */
  locked?: (row: any) => boolean
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
  /** Switches above the inputs, for sections whose switches reveal the inputs below them. */
  togglesFirst?: boolean
  /** Optional component rendered below the fields; receives the live `form` and the edited `row`. */
  extra?: Component
}

export interface ColumnDef<T> {
  key: string
  label: string
  /** Backend ordering field; enables sorting. */
  sorter?: string
  width?: number
  render?: (row: T) => VNodeChild
  /** Show the column only while this returns true. */
  visible?: () => boolean
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
  /** Show the rows in sections; the server sorts by the group's ordering first. */
  groupBy?: { ordering: string; key: (row: T) => string; label: (row: T) => VNodeChild }
  columns: ColumnDef<T>[]
  sections: FormSection[]
  filters?: FilterDef[]
  defaults: () => Record<string, unknown>
  /** Convert a row from the API into form values. */
  toForm: (row: T) => Record<string, unknown>
  /** Primary label of a record, used in titles and confirmations. */
  title: (row: T) => string
  /** Area of the role rights: reading shows the page, writing allows changes. */
  permission?: PermissionKey
  /** Only administrators see and change these records (e.g. roles). */
  superuser?: boolean
  /** Whether a record offers deleting; by default all do. */
  deletable?: (row: T) => boolean
}

export const isVisible = (def: { visible?: () => boolean }) => def.visible?.() ?? true

/** Whether a form field shows for the current form values. */
export const isFieldVisible = (field: FieldDef, form: Record<string, any>) =>
  field.visible?.(form) ?? true

/** The i18n key of a field's explanation, if any. */
export const helpKey = (field: FieldDef) =>
  typeof field.help === 'function' ? field.help() : field.help

export function sectionFields(resource: ResourceDef<any>): FieldDef[] {
  return resource.sections.flatMap((section) => section.fields)
}

export function defineResource<T extends { id: Id }>(def: ResourceDef<T>): ResourceDef<T> {
  return def
}
