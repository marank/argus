import { Check, Minus } from '@lucide/vue'
import { h } from 'vue'

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

export const text = (value: string | null | undefined) => value || '—'

export const withIcon = (icon: string, label: string) =>
  h('span', { class: 'row' }, [h(categoryIcon(icon), { size: 15, class: 'muted' }), label])
