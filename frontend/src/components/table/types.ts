import type { DataTableBaseColumn } from 'naive-ui'
import type { VNodeChild } from 'vue'

import type { ListParams, Page } from '@/types/common'

/* eslint-disable @typescript-eslint/no-explicit-any */

/**
 * A column of a list table. The `key` names the column in the saved view settings
 * (visibility, width, order) and, with `sorter`, is the backend ordering field.
 */
export type TableColumn<T> = Omit<DataTableBaseColumn<T>, 'key' | 'title'> & {
  key: string
  /** Translated header; columns without one (row actions) stay last and always show. */
  title: string
  /** Whether the column can be hidden; default true. */
  hideable?: boolean
  /** Hidden until the user shows it. */
  hidden?: boolean
}

/** A way to show the rows in sections; the server sorts by `ordering` first. */
export interface TableGrouping<T> {
  key: string
  /** Translated name in the grouping menu. */
  label: string
  /** Backend ordering that keeps the rows of a section together. */
  ordering: string
  /** Section of a row. */
  rowKey: (row: T) => string
  /** Header of a section, from its first row. */
  rowLabel: (row: T) => VNodeChild
}

export interface FilterOption {
  value: string
  label: string
}

/** A filter of the filter panel; `key` is the key in the list's filters. */
export type TableFilter = {
  key: string
  /** Translated label. */
  label: string
} &
  /** Several values may be chosen, as for entities. */
  (
    | { type: 'select'; options: FilterOption[] }
    | {
        type: 'entity'
        fetcher: (params: ListParams) => Promise<Page<any>>
        display: (item: any) => string
        params?: ListParams
      }
    /** Yes / no, sent as 'true' / 'false'. */
    | { type: 'boolean' }
    /**
     * A span of days, typed as text ("0611..2311", see `utils/dateRange`); sent as the ISO
     * dates `from` and `until` (filter keys of the list), either of which may stay open.
     */
    | { type: 'daterange'; from: string; until: string }
    /** A switch: choosing it sets the filter to `on()`; removing it clears the filter. */
    | { type: 'toggle'; on: () => unknown }
  )
