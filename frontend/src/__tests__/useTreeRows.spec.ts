import { describe, expect, it, vi } from 'vitest'

import { useTreeRows } from '@/composables/useTreeRows'

interface Row {
  id: string
  parent: string | null
  group?: string
}

const tree = (rows: Row[], grouped = false) =>
  useTreeRows<Row>({
    rows: () => rows,
    parent: (row) => row.parent,
    group: grouped ? (row) => row.group! : undefined,
    enabled: () => true,
  })

describe('useTreeRows', () => {
  it('places each row at its level with the lines that run past it', () => {
    // Operations > (Support, Logistics > (Inbound, Outbound)), Sales
    const { meta } = tree([
      { id: 'operations', parent: null },
      { id: 'support', parent: 'operations' },
      { id: 'logistics', parent: 'operations' },
      { id: 'inbound', parent: 'logistics' },
      { id: 'outbound', parent: 'logistics' },
      { id: 'sales', parent: null },
    ])
    const at = (id: string) => meta.value.get(id)!

    expect(at('operations')).toMatchObject({ depth: 0, hasChildren: true, last: false })
    expect(at('support')).toMatchObject({ depth: 1, last: false, through: [] })
    expect(at('logistics')).toMatchObject({ depth: 1, last: true, hasChildren: true })
    // Logistics is the last child, so no line of Operations's runs past Inbound and Outbound.
    expect(at('inbound')).toMatchObject({ depth: 2, last: false, through: [false] })
    expect(at('outbound')).toMatchObject({ depth: 2, last: true, through: [false] })
    expect(at('sales')).toMatchObject({ depth: 0, rootLast: true })
  })

  it('treats rows whose parent is not shown as top-level', () => {
    const { depth } = tree([
      { id: 'logistics', parent: 'operations' },
      { id: 'outbound', parent: 'logistics' },
    ])
    expect(depth({ id: 'logistics', parent: 'operations' })).toBe(0)
    expect(depth({ id: 'outbound', parent: 'logistics' })).toBe(1)
  })

  it('ends the group line at the last top-level row of each group', () => {
    const { meta, rowClass } = tree(
      [
        { id: 'laptops', parent: null, group: 'hardware' },
        { id: 'monitors', parent: null, group: 'hardware' },
        { id: 'arms', parent: 'monitors', group: 'hardware' },
        { id: 'office', parent: null, group: 'software' },
      ],
      true,
    )
    expect(rowClass({ id: 'monitors', parent: null })).toBe('tree-root-last')
    expect(rowClass({ id: 'arms', parent: 'monitors' })).toBe('tree-nested tree-tail')
    expect(meta.value.get('office')).toMatchObject({ rootLast: true, tail: false })
  })

  it('hides the rows below a collapsed row, unless collapsing is off', () => {
    vi.useFakeTimers()
    let collapsible = true
    const rows: Row[] = [
      { id: 'operations', parent: null },
      { id: 'logistics', parent: 'operations' },
      { id: 'outbound', parent: 'logistics' },
      { id: 'sales', parent: null },
    ]
    const { isShown, toggle, meta } = useTreeRows<Row>({
      rows: () => rows,
      parent: (row) => row.parent,
      enabled: () => true,
      collapsible: () => collapsible,
    })
    const shown = () => rows.filter(isShown).map((row) => row.id)

    toggle('operations')
    expect(shown()).toEqual(['operations', 'logistics', 'outbound', 'sales'])
    vi.advanceTimersByTime(200)
    expect(shown()).toEqual(['operations', 'sales'])
    // The collapsed row keeps its children (and so its chevron).
    expect(meta.value.get('operations')!.hasChildren).toBe(true)

    collapsible = false
    expect(shown()).toEqual(['operations', 'logistics', 'outbound', 'sales'])
    collapsible = true

    toggle('operations')
    expect(shown()).toEqual(['operations', 'logistics', 'outbound', 'sales'])
    vi.useRealTimers()
  })
})
