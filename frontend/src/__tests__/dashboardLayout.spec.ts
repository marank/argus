import { describe, expect, it } from 'vitest'
import type { Schemas } from '@/api/types'

import {
  defaultLayout,
  isDefaultLayout,
  mergeOrder,
  newInstance,
  moveBefore,
  resolveLayout,
  widgetType,
} from '@/components/dashboard/widgets'

const defs = [
  { id: 'a', size: 'large' as const },
  { id: 'b', size: 'medium' as const },
  { id: 'c', size: 'small' as const },
]
const widget = (
  id: string,
  extra: Partial<Schemas['DashboardWidgetOut']> = {},
): Schemas['DashboardWidgetOut'] => ({
  id,
  widget: null,
  visible: true,
  size: 'large',
  height: 'auto',
  hidden_cards: [],
  card_order: [],
  options: {},
  ...extra,
})

describe('dashboard layout', () => {
  it('falls back to the default without a saved layout', () => {
    expect(resolveLayout(defs, undefined)).toEqual(defaultLayout(defs))
    expect(resolveLayout(defs, [])).toEqual(defaultLayout(defs))
  })

  it('keeps the saved order, sizes and hidden cards', () => {
    const saved = [
      widget('c', { size: 'medium' }),
      widget('a', { visible: false, hidden_cards: ['x'] }),
      widget('b'),
    ]
    expect(resolveLayout(defs, saved)).toEqual(saved)
  })

  it('drops widgets that no longer exist', () => {
    const layout = resolveLayout(defs, [widget('b'), widget('gone'), widget('a'), widget('c')])
    expect(layout.map((w) => w.id)).toEqual(['b', 'a', 'c'])
  })

  it('adds new widgets behind their default predecessor', () => {
    expect(resolveLayout(defs, [widget('c'), widget('a')]).map((w) => w.id)).toEqual([
      'c',
      'a',
      'b',
    ])
    expect(resolveLayout(defs, [widget('c'), widget('b')]).map((w) => w.id)).toEqual([
      'a',
      'c',
      'b',
    ])
  })

  it('recognises the default layout', () => {
    expect(isDefaultLayout(defs, defaultLayout(defs))).toBe(true)
    expect(
      isDefaultLayout(defs, resolveLayout(defs, [widget('b'), widget('a'), widget('c')])),
    ).toBe(false)
  })
})

describe('card order', () => {
  it('applies a saved order and adds new cards behind their predecessor', () => {
    expect(mergeOrder(['x', 'y', 'z'], [])).toEqual(['x', 'y', 'z'])
    expect(mergeOrder(['x', 'y', 'z'], ['z', 'x'])).toEqual(['z', 'x', 'y'])
    expect(mergeOrder(['x', 'y'], ['gone', 'y', 'y', 'x'])).toEqual(['y', 'x'])
  })

  it('moves a card onto the place of another', () => {
    expect(moveBefore(['a', 'b', 'c', 'd'], 'a', 'c')).toEqual(['b', 'c', 'a', 'd'])
    expect(moveBefore(['a', 'b', 'c', 'd'], 'd', 'b')).toEqual(['a', 'd', 'b', 'c'])
    expect(moveBefore(['a', 'b'], 'a', 'missing')).toEqual(['a', 'b'])
  })
})

describe('optional widgets', () => {
  const withOptional = [...defs, { id: 'notes', size: 'small' as const, optional: true }]

  it('are off by default', () => {
    const notes = defaultLayout(withOptional).find((w) => w.id === 'notes')
    expect(notes?.visible).toBe(false)
    expect(isDefaultLayout(withOptional, defaultLayout(withOptional))).toBe(true)
  })

  it('join older layouts switched off', () => {
    const layout = resolveLayout(withOptional, [widget('a'), widget('b'), widget('c')])
    expect(layout.find((w) => w.id === 'notes')).toMatchObject({ visible: false, options: {} })
  })

  it('keep their options', () => {
    const saved = [widget('notes', { options: { text: 'Call Paul' } })]
    expect(resolveLayout(withOptional, saved).find((w) => w.id === 'notes')?.options).toEqual({
      text: 'Call Paul',
    })
  })
})

describe('further instances', () => {
  const withMultiple = [
    ...defs,
    { id: 'week', size: 'large' as const, optional: true, multiple: true },
  ]

  it('keep their place, widget and options', () => {
    const copy = widget('week~x1', { widget: 'week', options: { title: 'Counter' } })
    const layout = resolveLayout(withMultiple, [widget('a'), copy, widget('b'), widget('c')])
    expect(layout.map((w) => w.id)).toEqual(['a', 'week~x1', 'b', 'c', 'week'])
    expect(layout[1]).toEqual(copy)
    expect(widgetType(layout[1]!)).toBe('week')
  })

  it('go when their widget is gone or allows only one', () => {
    const saved = [
      widget('a'),
      widget('gone~x1', { widget: 'gone' }),
      widget('b~x2', { widget: 'b' }),
    ]
    expect(resolveLayout(withMultiple, saved).map((w) => w.id)).toEqual(['a', 'b', 'c', 'week'])
  })

  it('are new entries of the same widget', () => {
    const copy = newInstance(withMultiple[3]!)
    expect(copy).toMatchObject({ widget: 'week', visible: true, size: 'large', options: {} })
    expect(copy.id).toMatch(/^week~/)
    expect(newInstance(withMultiple[3]!).id).not.toBe(copy.id)
  })
})
