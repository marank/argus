import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { isVNode, nextTick, type VNode } from 'vue'

import {
  isGroupRow,
  useGroupedRows,
  withGroupHeaders,
  type GroupRow,
} from '@/composables/useGroupedRows'

interface Row {
  id: string
  group: string
  hidden?: boolean
}

const ROWS: Row[] = [
  { id: 'a1', group: 'A' },
  { id: 'a2', group: 'A' },
  { id: 'b1', group: 'B' },
]

function grouped(options: { enabled?: () => boolean; storageKey?: string; rows?: Row[] } = {}) {
  return useGroupedRows<Row>({
    rows: () => options.rows ?? ROWS,
    key: (row) => row.group,
    label: (row) => `Group ${row.group}`,
    visible: (row) => !row.hidden,
    enabled: options.enabled,
    storageKey: options.storageKey,
  })
}

const ids = (rows: (Row | GroupRow)[]) => rows.map((row) => (isGroupRow(row) ? row.id : row.id))

describe('useGroupedRows', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    localStorage.clear()
  })
  afterEach(() => vi.useRealTimers())

  it('puts a header with the count before each group', () => {
    const { rows } = grouped()
    expect(ids(rows.value)).toEqual(['group:A', 'a1', 'a2', 'group:B', 'b1'])
    const header = rows.value[0] as GroupRow
    expect(header).toMatchObject({ key: 'A', label: 'Group A', count: 2, collapsed: false })
  })

  it('counts hidden rows for their group without showing them', () => {
    const { rows } = grouped({
      rows: [
        { id: 'a1', group: 'A' },
        { id: 'a2', group: 'A', hidden: true },
      ],
    })
    expect(ids(rows.value)).toEqual(['group:A', 'a1'])
    expect((rows.value[0] as GroupRow).count).toBe(2)
  })

  it('shows the plain visible rows when grouping is off', () => {
    const { rows, rowClass } = grouped({
      enabled: () => false,
      rows: [...ROWS, { id: 'b2', group: 'B', hidden: true }],
    })
    expect(ids(rows.value)).toEqual(['a1', 'a2', 'b1'])
    expect(rowClass(ROWS[0]!)).toBe('')
  })

  it('collapses a group after its rows faded out', () => {
    const { rows, toggle, rowClass, collapsed } = grouped()
    toggle('A')
    expect(rowClass(ROWS[0]!)).toContain('group-child-leave')
    expect(ids(rows.value)).toContain('a1')
    vi.advanceTimersByTime(140)
    expect(collapsed.value).toEqual(['A'])
    expect(ids(rows.value)).toEqual(['group:A', 'group:B', 'b1'])
    expect((rows.value[0] as GroupRow).collapsed).toBe(true)
  })

  it('ignores toggles while a group is fading out', () => {
    const { toggle, collapsed } = grouped()
    toggle('A')
    toggle('B')
    vi.advanceTimersByTime(500)
    expect(collapsed.value).toEqual(['A'])
  })

  it('expands a collapsed group with an enter animation', () => {
    const { rows, toggle, rowClass, collapsed } = grouped()
    collapsed.value = ['A']
    toggle('A')
    expect(collapsed.value).toEqual([])
    expect(ids(rows.value)).toContain('a1')
    expect(rowClass(ROWS[0]!)).toContain('group-child-enter')
    vi.advanceTimersByTime(400)
    expect(rowClass(ROWS[0]!)).not.toContain('group-child-enter')
  })

  it('marks the last row of each group', () => {
    const { rows, rowClass } = grouped()
    void rows.value
    expect(rowClass(ROWS[0]!)).toBe('group-child')
    expect(rowClass(ROWS[1]!)).toBe('group-child group-child-last')
    expect(rowClass(ROWS[2]!)).toBe('group-child group-child-last')
    expect(rowClass(rows.value[0]!)).toBe('group-row')
  })

  it('remembers collapsed groups per table', async () => {
    const first = grouped({ storageKey: 'test.groups' })
    first.toggle('B')
    vi.advanceTimersByTime(140)
    await nextTick()
    const again = grouped({ storageKey: 'test.groups' })
    expect(again.collapsed.value).toEqual(['B'])
  })

  it('toggles headers by click, Enter and Space', () => {
    const { rows, rowProps, collapsed } = grouped()
    const header = rows.value[0]!
    const props = rowProps(header) as Record<string, unknown>
    expect(props).toMatchObject({ role: 'button', tabindex: 0, 'aria-expanded': true })

    const keydown = props.onKeydown as (event: KeyboardEvent) => void
    keydown(new KeyboardEvent('keydown', { key: 'a' }))
    vi.advanceTimersByTime(140)
    expect(collapsed.value).toEqual([])

    const enter = new KeyboardEvent('keydown', { key: 'Enter', cancelable: true })
    keydown(enter)
    expect(enter.defaultPrevented).toBe(true)
    vi.advanceTimersByTime(140)
    expect(collapsed.value).toEqual(['A'])

    keydown(new KeyboardEvent('keydown', { key: ' ' }))
    expect(collapsed.value).toEqual([])
    ;(props.onClick as () => void)()
    vi.advanceTimersByTime(140)
    expect(collapsed.value).toEqual(['A'])
  })

  it('passes clicks on other rows on', () => {
    const { rowProps } = grouped()
    const onRowClick = vi.fn<(row: Row) => void>()
    ;(rowProps(ROWS[2]!, onRowClick).onClick as () => void)()
    expect(onRowClick).toHaveBeenCalledWith(ROWS[2])
    expect(rowProps(ROWS[2]!)).toEqual({})
  })
})

describe('withGroupHeaders', () => {
  const header: GroupRow = {
    __group: true,
    id: 'group:A',
    key: 'A',
    label: 'Group A',
    count: 2,
    collapsed: false,
  }
  const columns = withGroupHeaders<Row>([
    { key: 'id', title: 'ID' },
    { key: 'group', title: 'Group', render: (row) => `<${row.group}>` },
  ]) as unknown as {
    colSpan?: (row: Row | GroupRow) => number
    render: (row: Row | GroupRow, index: number) => unknown
  }[]

  it('lets the first column span the header row', () => {
    expect(columns[0]!.colSpan!(header)).toBe(2)
    expect(columns[0]!.colSpan!(ROWS[0]!)).toBe(1)
    expect(columns[1]!.colSpan).toBeUndefined()
  })

  it('renders the label and count in the first column only', () => {
    const node = columns[0]!.render(header, 0) as VNode
    expect(isVNode(node)).toBe(true)
    const children = node.children as unknown[]
    expect(children[0]).toBe('Group A')
    expect((children[1] as VNode).children).toBe('2')
    expect(columns[1]!.render(header, 0)).toBeNull()
  })

  it('renders ordinary rows as before', () => {
    expect(columns[0]!.render(ROWS[0]!, 0)).toBe('a1')
    expect(columns[1]!.render(ROWS[0]!, 0)).toBe('<A>')
  })
})
