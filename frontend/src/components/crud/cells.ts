import { Check, CornerDownRight, Minus } from '@lucide/vue'
import { h, type VNodeChild } from 'vue'

import { categoryIcon } from '@/utils/icons'

/** Small render helpers for resource table columns. */
export const mono = (value: string | number | null | undefined) =>
  h(
    'span',
    { class: 'mono' },
    value === null || value === undefined || value === '' ? '—' : String(value),
  )

export const bool = (value: boolean) =>
  value ? h(Check, { size: 15, class: 'cell-yes' }) : h(Minus, { size: 15, class: 'muted' })

/** A value taken over from elsewhere (a parent, the category): greyed out behind a corner arrow. */
export const inherited = (value: VNodeChild, title: string) =>
  h('span', { class: 'row muted', style: 'gap:3px', title }, [
    h(CornerDownRight, { size: 11 }),
    value,
  ])

/** The own value, otherwise the one that applies from elsewhere, otherwise a dash. */
export const ownOrInherited = (
  own: string | null | undefined,
  effective: string | null | undefined,
  title: string,
) => own || (effective ? inherited(effective, title) : '—')

export const text = (value: string | null | undefined) => value || '—'

/** A record's path, e.g. “Operations / Logistics”: the records above it greyed out. */
export const path = (names: string[]) =>
  names.length > 1
    ? h('span', [
        h('span', { class: 'muted' }, `${names.slice(0, -1).join(' / ')} / `),
        names.at(-1),
      ])
    : (names[0] ?? '—')

export const withIcon = (icon: string, label: VNodeChild) =>
  h('span', { class: 'row' }, [h(categoryIcon(icon), { size: 15, class: 'muted' }), label])
