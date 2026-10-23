import { ChevronDown } from '@lucide/vue'
import { useStorage } from '@vueuse/core'
import { computed, h, ref, type VNodeChild } from 'vue'

import type { Id } from '@/types/common'

/** Indent per tree level, as for the rows of a group (see base.css). */
const INDENT = 24

/** Where a row sits in the tree of the rows shown. */
interface TreeMeta {
  /** 0 for top-level rows and for rows whose parent is not shown. */
  depth: number
  /** Per level above the own one: whether the line of that level runs on past this row. */
  through: boolean[]
  /** Last child of its parent among the rows shown. */
  last: boolean
  hasChildren: boolean
  /** The rows above it, the nearest last. */
  ancestors: Id[]
  /** Last top-level row of its group; nested rows after it are the group's tail. */
  rootLast: boolean
  tail: boolean
}

/**
 * Tree view of hierarchical rows, such as departments or categories. The rows must
 * come parents first, each followed by the rows below it (the server's `tree_position`)
 * and, in grouped tables, already sorted by group. A row whose parent is not shown
 * (search, filter, page break) counts as top-level.
 *
 * Rows with children can be collapsed by the chevron after their label; collapsed rows
 * are remembered per table when `storageKey` is given.
 */
export function useTreeRows<T extends { id: Id }>(options: {
  rows: () => T[]
  parent: (row: T) => Id | null | undefined
  /** Group of a row in grouped tables; a parent in another group does not count. */
  group?: (row: T) => string
  enabled: () => boolean
  /** Whether collapsed rows hide the rows below them (e.g. not while searching). */
  collapsible?: () => boolean
  storageKey?: string
}) {
  const collapsed = options.storageKey ? useStorage<Id[]>(options.storageKey, []) : ref<Id[]>([])
  const collapsible = () => options.collapsible?.() ?? true
  const isCollapsed = (id: Id) => collapsible() && collapsed.value.includes(id)

  const meta = computed(() => {
    const result = new Map<Id, TreeMeta>()
    if (!options.enabled()) return result
    const rows = options.rows()
    const groupOf = (row: T) => options.group?.(row) ?? ''

    // Only parents shown before the row count, which also stops at a loop in the data.
    const shown = new Map<Id, T>()
    const parentOf = new Map<Id, Id | null>()
    for (const row of rows) {
      const parent = shown.get(options.parent(row) ?? '')
      parentOf.set(row.id, parent && groupOf(parent) === groupOf(row) ? parent.id : null)
      shown.set(row.id, row)
    }
    const siblingsKey = (row: T) => parentOf.get(row.id) ?? `root:${groupOf(row)}`
    const lastChild = new Map<string, Id>()
    for (const row of rows) lastChild.set(siblingsKey(row), row.id)
    const isLast = (row: T) => lastChild.get(siblingsKey(row)) === row.id
    const parents = new Set(parentOf.values())

    const ancestors = new Map<Id, T[]>()
    const pastRootLast = new Set<string>()
    for (const row of rows) {
      const parentId = parentOf.get(row.id)
      const chain = parentId ? [...ancestors.get(parentId)!, shown.get(parentId)!] : []
      ancestors.set(row.id, chain)
      const rootLast = !parentId && isLast(row)
      result.set(row.id, {
        depth: chain.length,
        through: chain.slice(1).map((ancestor) => !isLast(ancestor)),
        last: isLast(row),
        hasChildren: parents.has(row.id),
        ancestors: chain.map((ancestor) => ancestor.id).reverse(),
        rootLast,
        tail: pastRootLast.has(groupOf(row)),
      })
      if (rootLast) pastRootLast.add(groupOf(row))
    }
    return result
  })

  const depth = (row: T) => meta.value.get(row.id)?.depth ?? 0

  /** Whether the row shows, i.e. no row above it is collapsed. */
  const isShown = (row: T) => !meta.value.get(row.id)?.ancestors.some(isCollapsed)

  /** Row whose children are animating in or out (see `.tree-enter/-leave`). */
  const entering = ref<Id | null>(null)
  const leaving = ref<Id | null>(null)
  const LEAVE_MS = 140

  function toggle(id: Id) {
    if (leaving.value) return
    if (collapsed.value.includes(id)) {
      collapsed.value = collapsed.value.filter((c) => c !== id)
      entering.value = id
      setTimeout(() => entering.value === id && (entering.value = null), 400)
    } else {
      // Let the rows fade out before they are removed.
      leaving.value = id
      setTimeout(() => {
        collapsed.value = [...collapsed.value, id]
        leaving.value = null
      }, LEAVE_MS)
    }
  }

  /** The cell content indented to its level, with the lines that lead to it. */
  function cell(row: T, content: VNodeChild): VNodeChild {
    const m = meta.value.get(row.id)
    if (!m) return content
    const left = (level: number) => ({ left: `calc(var(--tree-base) + ${level * INDENT + 7}px)` })
    return h('div', { class: 'tree-node', style: { paddingLeft: `${m.depth * INDENT}px` } }, [
      ...m.through.map((on, level) =>
        on ? h('span', { class: 'tree-line', style: left(level) }) : null,
      ),
      m.depth
        ? h('span', {
            class: ['tree-elbow', { 'tree-elbow-last': m.last }],
            style: left(m.depth - 1),
          })
        : null,
      m.hasChildren && !isCollapsed(row.id)
        ? h('span', { class: 'tree-stub', style: left(m.depth) })
        : null,
      h('span', { class: 'tree-label' }, [content]),
      m.hasChildren && collapsible() ? chevron(row.id) : null,
    ])
  }

  /** Toggles the rows below; a click on it does not open the row. */
  function chevron(id: Id) {
    const closed = isCollapsed(id)
    return h(
      'button',
      {
        type: 'button',
        class: ['tree-chevron', { collapsed: closed }],
        'aria-expanded': !closed,
        onClick: (event: Event) => (event.stopPropagation(), toggle(id)),
      },
      [h(ChevronDown, { size: 14 })],
    )
  }

  /** Classes that fit the lines of grouped tables to the tree (see base.css). */
  function rowClass(row: T): string {
    const m = meta.value.get(row.id)
    if (!m) return ''
    return [
      m.depth && 'tree-nested',
      m.rootLast && 'tree-root-last',
      m.tail && 'tree-tail',
      entering.value && m.ancestors.includes(entering.value) && 'tree-enter',
      leaving.value && m.ancestors.includes(leaving.value) && 'tree-leave',
    ]
      .filter(Boolean)
      .join(' ')
  }

  return { meta, depth, isShown, toggle, collapsed, cell, rowClass }
}
