import { describe, expect, it } from 'vitest'

import {
  defaultLayout,
  isDefaultLayout,
  mergeOrder,
  moveBefore,
  resolveLayout,
} from '@/components/dashboard/widgets'
import type { WidgetSettings } from '@/types/accounts'

const defs = [
  { id: 'a', size: 'large' as const },
  { id: 'b', size: 'medium' as const },
  { id: 'c', size: 'small' as const },
]
const widget = (id: string, extra: Partial<WidgetSettings> = {}): WidgetSettings => ({
  id,
  visible: true,
  size: 'large',
  hidden_cards: [],
  card_order: [],
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

  it('fills in the card order of layouts saved before it existed', () => {
    const old = {
      id: 'a',
      visible: true,
      size: 'large',
      hidden_cards: [],
    } as unknown as WidgetSettings
    expect(resolveLayout(defs, [old])[0]!.card_order).toEqual([])
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
