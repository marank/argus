import { useStorage } from '@vueuse/core'
import type { DataTableColumns, DataTableSize } from 'naive-ui'
import { computed } from 'vue'

import type { TableColumn, TableGrouping } from '@/components/table/types'
import { isGroupRow, useGroupedRows, withGroupHeaders, type GroupRow } from './useGroupedRows'

/** Width of columns that share the rest of the table, for the sideways scroll. */
const FLEX_WIDTH = 180
/** Narrowest a column gets by dragging its edge. */
const MIN_WIDTH = 60

/** What a user set up for a table, remembered per table in the browser. */
interface ViewSettings {
  /** Hidden columns; null: the columns' own defaults. */
  hidden: string[] | null
  /** Widths set by dragging a column edge. */
  widths: Record<string, number>
  /** Order of the movable columns; empty: as defined. */
  order: string[]
  /** Active grouping; null: none, undefined: the table's default. */
  group: string | null | undefined
  density: DataTableSize
}

const defaults = (): ViewSettings => ({
  hidden: null,
  widths: {},
  order: [],
  group: undefined,
  density: 'small',
})

/**
 * Columns the user can move: the titled ones that are not fixed to an edge. Key columns
 * (`hideable: false`, e.g. the name) stay first, which the tree view of master data needs.
 */
const isMovable = (column: { title: string; fixed?: string | false; hideable?: boolean }) =>
  !!column.title && !column.fixed && column.hideable !== false

const isFirst = (column: { title: string; fixed?: string | false; hideable?: boolean }) =>
  column.fixed === 'left' || (!!column.title && !column.fixed && column.hideable === false)

/**
 * The user's view of a list table: which columns show in which order and width, the
 * grouping and the row density, remembered per table under `id`. Bind it to a table with
 * `ListTable` and to its toolbar with `TableToolbar`; pass `groupOrdering` to `useList`.
 */
export function useTableView<T extends object>(options: {
  id: string
  columns: () => TableColumn<T>[]
  rows: () => T[]
  groupings?: () => TableGrouping<T>[]
  /** Grouping until the user picks one; none by default. */
  defaultGrouping?: string
  /** Rows to leave out though they count for their group (e.g. below a collapsed tree row). */
  visible?: (row: T) => boolean
  /** Extra classes for data rows (not group headers). */
  rowClass?: (row: T) => string
}) {
  const settings = useStorage<ViewSettings>(`argus.table.${options.id}`, defaults(), undefined, {
    mergeDefaults: true,
  })

  const groupings = computed(() => options.groupings?.() ?? [])
  const grouping = computed<TableGrouping<T> | null>(() => {
    const key = settings.value.group === undefined ? options.defaultGrouping : settings.value.group
    return groupings.value.find((g) => g.key === key) ?? null
  })

  /** Whether a column is hidden by the given list of hidden columns (null: the defaults). */
  function hiddenBy(column: TableColumn<T>, hidden: string[] | null) {
    if (column.hideable === false || !column.title) return false
    return hidden ? hidden.includes(column.key) : !!column.hidden
  }
  const isHidden = (column: TableColumn<T>) => hiddenBy(column, settings.value.hidden)

  /** Fixed and key columns first, then the movable ones in `order`, untitled ones last. */
  function arrange(all: TableColumn<T>[], order: string[]) {
    const rank = (column: TableColumn<T>) => {
      const index = order.indexOf(column.key)
      return index < 0 ? order.length + all.indexOf(column) : index
    }
    const movable = all.filter(isMovable).sort((a, b) => rank(a) - rank(b))
    return [...all.filter(isFirst), ...movable, ...all.filter((c) => !isMovable(c) && !isFirst(c))]
  }

  const ordered = computed(() => arrange(options.columns(), settings.value.order))

  const baseColumns = computed(() =>
    ordered.value
      .filter((column) => !isHidden(column))
      .map((column) => {
        const { hideable: _hideable, hidden: _hidden, ...rest } = column
        const width = settings.value.widths[column.key]
        if (!column.title) return rest
        return {
          ...rest,
          resizable: column.resizable ?? true,
          ...(width ? { width, minWidth: MIN_WIDTH } : {}),
          // A dragged edge may cut the text, so it ends in an ellipsis with the full text above.
          ellipsis: column.ellipsis ?? (width ? { tooltip: true } : undefined),
        }
      }),
  )

  const columns = computed(() => {
    const base = baseColumns.value as DataTableColumns<T>
    return grouping.value ? withGroupHeaders(base) : (base as DataTableColumns<T | GroupRow>)
  })

  /** Wide enough for every column; narrower screens scroll the table sideways. */
  const scrollX = computed(() =>
    baseColumns.value.reduce((sum, column) => {
      const width = column.width ?? column.minWidth ?? FLEX_WIDTH
      return sum + (typeof width === 'number' ? width : parseInt(width, 10) || FLEX_WIDTH)
    }, 0),
  )

  const grouped = useGroupedRows<T>({
    rows: options.rows,
    key: (row) => grouping.value!.rowKey(row),
    label: (row) => grouping.value!.rowLabel(row),
    enabled: () => !!grouping.value,
    visible: options.visible,
    storageKey: `argus.groups.${options.id}`,
  })

  const rowClass = (row: T | GroupRow) =>
    [grouped.rowClass(row), !isGroupRow(row) && options.rowClass?.(row)].filter(Boolean).join(' ')

  /** The columns as the column settings list them. */
  const settingColumns = computed(() =>
    ordered.value
      .filter((column) => column.title)
      .map((column) => ({
        key: column.key,
        title: column.title,
        visible: !isHidden(column),
        hideable: column.hideable !== false,
        movable: isMovable(column),
      })),
  )

  function setVisible(key: string, visible: boolean) {
    const column = ordered.value.find((c) => c.key === key)
    if (!column || column.hideable === false || !column.title) return
    const hidden = new Set(
      settings.value.hidden ?? ordered.value.filter((c) => c.hidden).map((c) => c.key),
    )
    if (visible) hidden.delete(key)
    else hidden.add(key)
    settings.value.hidden = [...hidden]
  }

  /** Takes over the order of the movable columns among `keys` (e.g. the column settings list). */
  function setOrder(keys: string[]) {
    const movable = new Set(ordered.value.filter(isMovable).map((c) => c.key))
    settings.value.order = keys.filter((key) => movable.has(key))
  }

  function onResize(_width: number, limited: number, column: { key: string | number }) {
    settings.value.widths = { ...settings.value.widths, [column.key]: Math.round(limited) }
  }

  /**
   * Whether the table looks other than by default: other columns or another column order,
   * dragged widths, another grouping or row height. Settings that change nothing visible
   * (e.g. the order of hidden columns) do not count.
   */
  const customized = computed(() => {
    const shown = (columns: TableColumn<T>[], hidden: string[] | null) =>
      columns
        .filter((c) => !hiddenBy(c, hidden))
        .map((c) => c.key)
        .join()
    const all = options.columns()
    return (
      shown(ordered.value, settings.value.hidden) !== shown(arrange(all, []), null) ||
      Object.keys(settings.value.widths).length > 0 ||
      (grouping.value?.key ?? null) !== (options.defaultGrouping ?? null) ||
      settings.value.density !== 'small'
    )
  })

  function reset() {
    settings.value = defaults()
  }

  return {
    columns,
    rows: grouped.rows,
    rowProps: grouped.rowProps,
    rowClass,
    scrollX,
    groupings,
    grouping,
    /** Ordering for `useList`, which reloads when it changes. */
    groupOrdering: () => grouping.value?.ordering,
    setGrouping: (key: string | null) => (settings.value.group = key),
    density: computed(() => settings.value.density),
    setDensity: (value: DataTableSize) => (settings.value.density = value),
    settingColumns,
    setVisible,
    setOrder,
    onResize,
    customized,
    reset,
  }
}

export type TableView<T extends object> = ReturnType<typeof useTableView<T>>
