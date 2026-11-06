import type { Component, VNodeChild } from 'vue'
import type { Schemas } from '@/api/types'

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
    | {
        type: 'icon'
        /** Icons to choose from, by stored name; the category icons by default. */
        icons?: Record<string, Component>
        /** Enum group (see enums.ts) that names the icons; otherwise their stored names show. */
        group?: string
      }
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
  /** Show the section only while this returns true; gets the live form. */
  visible?: (form: Record<string, any>) => boolean
  /** Switches above the inputs, for sections whose switches reveal the inputs below them. */
  togglesFirst?: boolean
  /**
   * Optional component rendered below the fields; receives the live `form` and the edited `row`
   * and may emit `set(key, value)` to change a form value.
   */
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
  /** Hidden until shown in the column settings. */
  hidden?: boolean
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
    remove: (id: Id) => Promise<true>
  }
  ordering?: string
  /**
   * Ways to show the rows in sections, chosen in the toolbar; the first is the default.
   * The server sorts by the grouping's ordering first.
   */
  groupings?: {
    key: string
    /** i18n key of the name in the grouping menu. */
    label: string
    ordering: string
    rowKey: (row: T) => string
    rowLabel: (row: T) => VNodeChild
  }[]
  /**
   * Offer a tree view of hierarchical records: the first column indents each record below
   * its parent and shows `label` instead (the column's own content, e.g. the path, stays
   * for records whose parent is not on the page).
   */
  tree?: {
    /** Backend ordering that puts each record right after its parent. */
    ordering: string
    parent: (row: T) => Id | null | undefined
    label: (row: T) => VNodeChild
  }
  columns: ColumnDef<T>[]
  sections: FormSection[]
  filters?: FilterDef[]
  defaults: () => Record<string, unknown>
  /** Convert a row from the API into form values. */
  toForm: (row: T) => Record<string, unknown>
  /** Primary label of a record, used in titles and confirmations. */
  title: (row: T) => string
  /** Area of the role rights: reading shows the page, writing allows changes. */
  permission?: Schemas['ResourceKey']
  /** Only administrators see and change these records (e.g. roles). */
  superuser?: boolean
  /** Whether a record offers deleting; by default all do. */
  deletable?: (row: T) => boolean
  /**
   * New records that build on an existing one, e.g. a successor model. A row action creates one
   * with the `copy` fields taken over and the original in the `link` field; choosing a record in
   * the `link` field of the form offers to take over the `copy` fields as well.
   */
  derive?: {
    /** i18n key of the row action. */
    label: string
    icon: Component
    link: string
    copy: string[]
  }
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
