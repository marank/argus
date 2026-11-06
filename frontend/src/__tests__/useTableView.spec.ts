import { beforeEach, describe, expect, it } from 'vitest'
import { nextTick, ref } from 'vue'

import type { TableColumn, TableGrouping } from '@/components/table/types'
import { isGroupRow } from '@/composables/useGroupedRows'
import { useTableView } from '@/composables/useTableView'

interface Row {
  id: string
  name: string
  kind: string
}

const ROWS: Row[] = [
  { id: 'r1', name: 'One', kind: 'a' },
  { id: 'r2', name: 'Two', kind: 'b' },
]

const COLUMNS: TableColumn<Row>[] = [
  { key: 'name', title: 'Name', hideable: false, minWidth: 200 },
  { key: 'kind', title: 'Kind', width: 100 },
  { key: 'notes', title: 'Notes', width: 150, hidden: true },
  { key: 'extra', title: 'Extra', width: 80 },
  { key: '_actions', title: '', width: 40 },
]

const GROUPINGS: TableGrouping<Row>[] = [
  { key: 'kind', label: 'Kind', ordering: 'kind', rowKey: (r) => r.kind, rowLabel: (r) => r.kind },
]

function view(options: { defaultGrouping?: string; columns?: TableColumn<Row>[] } = {}) {
  return useTableView<Row>({
    id: 'test',
    columns: () => options.columns ?? COLUMNS,
    rows: () => ROWS,
    groupings: () => GROUPINGS,
    defaultGrouping: options.defaultGrouping,
    rowClass: (row) => `row-${row.id}`,
  })
}

const keys = (v: ReturnType<typeof view>) => v.columns.value.map((c) => ('key' in c ? c.key : ''))

describe('useTableView', () => {
  beforeEach(() => localStorage.clear())

  it('shows the columns as defined, without the hidden ones', () => {
    const v = view()
    expect(keys(v)).toEqual(['name', 'kind', 'extra', '_actions'])
    expect(v.scrollX.value).toBe(200 + 100 + 80 + 40)
    expect(v.customized.value).toBe(false)
  })

  it('shows and hides columns, but never key columns', async () => {
    const v = view()
    v.setVisible('notes', true)
    v.setVisible('kind', false)
    v.setVisible('name', false)
    expect(keys(v)).toEqual(['name', 'notes', 'extra', '_actions'])
    expect(v.settingColumns.value.find((c) => c.key === 'name')).toMatchObject({
      hideable: false,
      movable: false,
    })
    await nextTick()
    expect(JSON.parse(localStorage.getItem('argus.table.test')!).hidden).toEqual(['kind'])
  })

  it('orders the movable columns and keeps key and action columns in place', () => {
    const v = view()
    v.setOrder(['_actions', 'extra', 'name', 'kind', 'gone'])
    expect(keys(v)).toEqual(['name', 'extra', 'kind', '_actions'])
    v.setVisible('notes', true)
    // Columns missing from the order follow in their own order.
    expect(keys(v)).toEqual(['name', 'extra', 'kind', 'notes', '_actions'])
  })

  it('keeps a dragged width and lets the column shrink below its own minimum', () => {
    const v = view()
    v.onResize(123.4, 120.6, { key: 'name' })
    const name = v.columns.value[0] as TableColumn<Row>
    expect(name).toMatchObject({ width: 121, minWidth: 60, resizable: true })
    expect(name.ellipsis).toEqual({ tooltip: true })
    expect(v.columns.value.at(-1)).not.toHaveProperty('resizable')
  })

  it('groups by the default grouping until the user picks another', () => {
    const v = view({ defaultGrouping: 'kind' })
    expect(v.groupOrdering()).toBe('kind')
    expect(v.rows.value.filter(isGroupRow).map((g) => g.key)).toEqual(['a', 'b'])
    expect(v.rowClass(ROWS[0]!)).toContain('row-r1')
    v.setGrouping(null)
    expect(v.groupOrdering()).toBeUndefined()
    expect(v.rows.value).toEqual(ROWS)
    v.setGrouping('gone')
    expect(v.grouping.value).toBeNull()
  })

  it('remembers the row density and resets everything', () => {
    const v = view()
    v.setDensity('medium')
    v.setVisible('kind', false)
    expect(v.density.value).toBe('medium')
    expect(v.customized.value).toBe(true)
    v.reset()
    expect(v.density.value).toBe('small')
    expect(keys(v)).toEqual(['name', 'kind', 'extra', '_actions'])
  })

  it('counts as changed only what changes the table', () => {
    const v = view({ defaultGrouping: 'kind' })
    // Hiding and showing again, or ordering hidden columns, leaves the table as it was.
    v.setVisible('kind', false)
    v.setVisible('kind', true)
    v.setOrder(['notes', 'kind', 'extra'])
    v.setGrouping('kind')
    expect(v.customized.value).toBe(false)
    v.setOrder(['extra', 'kind'])
    expect(v.customized.value).toBe(true)
    v.reset()
    v.setGrouping(null)
    expect(v.customized.value).toBe(true)
  })

  it('follows changed column definitions', () => {
    const columns = ref<TableColumn<Row>[]>(COLUMNS)
    const v = useTableView<Row>({ id: 'live', columns: () => columns.value, rows: () => ROWS })
    columns.value = [{ key: 'name', title: 'Name', width: '120px' as unknown as number }]
    expect(keys(v)).toEqual(['name'])
    expect(v.scrollX.value).toBe(120)
  })
})
