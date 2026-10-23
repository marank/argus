import { ChevronDown } from '@lucide/vue'
import { useStorage } from '@vueuse/core'
import type { DataTableColumns } from 'naive-ui'
import { computed, h, ref, type HTMLAttributes, type VNodeChild } from 'vue'

/** Section header inserted between the rows of a grouped table. */
export interface GroupRow {
  __group: true
  id: string
  key: string
  label: VNodeChild
  /** Rows of this group on the current page. */
  count: number
  collapsed: boolean
}

export const isGroupRow = (row: unknown): row is GroupRow =>
  typeof row === 'object' && row !== null && '__group' in row

/**
 * Rows of a table in collapsible sections. The rows must already be sorted by
 * group (the server orders by the group first, see `useList`). Collapsed groups
 * are remembered per table when `storageKey` is given.
 */
export function useGroupedRows<T extends object>(options: {
  rows: () => T[]
  key: (row: T) => string
  label: (row: T) => VNodeChild
  enabled?: () => boolean
  /** Rows to leave out though they count for their group (e.g. below a collapsed tree row). */
  visible?: (row: T) => boolean
  storageKey?: string
}) {
  const collapsed = options.storageKey
    ? useStorage<string[]>(options.storageKey, [])
    : ref<string[]>([])
  let lastInGroup = new WeakSet<object>()

  const rows = computed<(T | GroupRow)[]>(() => {
    const source = options.rows()
    if (options.enabled && !options.enabled())
      return options.visible ? source.filter(options.visible) : source
    const result: (T | GroupRow)[] = []
    const last = new WeakSet<object>()
    let header = null as GroupRow | null
    let previous = null as T | null
    for (const row of source) {
      const key = options.key(row)
      if (key !== header?.key) {
        if (previous) last.add(previous)
        header = {
          __group: true,
          id: `group:${key}`,
          key,
          label: options.label(row),
          count: 0,
          collapsed: collapsed.value.includes(key),
        }
        result.push(header)
      }
      header.count += 1
      if (!header.collapsed && (options.visible?.(row) ?? true)) result.push(row)
      previous = row
    }
    if (previous) last.add(previous)
    lastInGroup = last
    return result
  })

  /** Group whose rows are animating in or out (see `.group-child-enter/-leave`). */
  const entering = ref<string | null>(null)
  const leaving = ref<string | null>(null)
  const LEAVE_MS = 140

  function toggle(key: string) {
    if (leaving.value) return
    if (collapsed.value.includes(key)) {
      collapsed.value = collapsed.value.filter((k) => k !== key)
      entering.value = key
      setTimeout(() => entering.value === key && (entering.value = null), 400)
    } else {
      // Let the rows fade out before they are removed.
      leaving.value = key
      setTimeout(() => {
        collapsed.value = [...collapsed.value, key]
        leaving.value = null
      }, LEAVE_MS)
    }
  }

  /** Group headers toggle on click and Enter/Space; other rows get `onRowClick`. */
  function rowProps(row: T | GroupRow, onRowClick?: (row: T) => void): HTMLAttributes {
    if (isGroupRow(row)) {
      return {
        tabindex: 0,
        role: 'button',
        'aria-expanded': !row.collapsed,
        onClick: () => toggle(row.key),
        onKeydown: (event: KeyboardEvent) => {
          if (event.key !== 'Enter' && event.key !== ' ') return
          event.preventDefault()
          toggle(row.key)
        },
      }
    }
    return onRowClick ? { onClick: () => onRowClick(row) } : {}
  }

  function rowClass(row: T | GroupRow): string {
    if (isGroupRow(row)) return 'group-row'
    if (options.enabled && !options.enabled()) return ''
    const classes = ['group-child']
    if (lastInGroup.has(row)) classes.push('group-child-last')
    const key = options.key(row as T)
    if (key === entering.value) classes.push('group-child-enter')
    if (key === leaving.value) classes.push('group-child-leave')
    return classes.join(' ')
  }

  return { rows, rowProps, rowClass, toggle, collapsed }
}

/** Let the first column span the whole row for group headers. */
export function withGroupHeaders<T>(columns: DataTableColumns<T>): DataTableColumns<T | GroupRow> {
  const span = columns.length
  return columns.map((column, index) => {
    const original = 'render' in column ? column.render : undefined
    return {
      ...column,
      colSpan: index === 0 ? (row: T | GroupRow) => (isGroupRow(row) ? span : 1) : undefined,
      render: (row: T | GroupRow, rowIndex: number) => {
        if (isGroupRow(row)) {
          if (index !== 0) return null
          // Icon first (above the tree lines), the toggle arrow on the right.
          return h('div', { class: 'group-label' }, [
            row.label,
            h('span', { class: 'group-count mono' }, String(row.count)),
            h(ChevronDown, {
              size: 14,
              class: ['group-chevron', { collapsed: row.collapsed }],
            }),
          ])
        }
        if (original) return (original as (r: T, i: number) => VNodeChild)(row, rowIndex)
        const key = 'key' in column ? String(column.key) : ''
        return (row as Record<string, unknown>)[key] as VNodeChild
      },
    }
  }) as DataTableColumns<T | GroupRow>
}
