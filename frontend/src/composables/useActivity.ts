import { useI18n } from 'vue-i18n'

import { useFormat } from '@/composables/useFormat'
import type { Activity } from '@/types/activity'

/** Kinds that are one device, consumable or seat each, named in the detail. */
const ALLOCATION_KINDS = new Set<Activity['kind']>(['request_allocated', 'request_released'])

/** Texts of a row of the activity log, shared by the dashboard and the page. */
export function useActivity() {
  const { t } = useI18n()
  const { enumLabel } = useFormat()

  /** What the quantity counts: positions of a request or order, devices, delivered units, stock. */
  const quantity = (row: Activity): string => {
    const n = row.quantity
    if (n === null) return ''
    // The step already says the direction; only a correction needs its sign.
    if (row.kind === 'consumable_adjustment')
      return t('activity.stock', { count: n > 0 ? `+${n}` : `${n}` })
    if (row.area === 'consumables') return t('activity.stock', { count: Math.abs(n) })
    if (row.kind === 'order_received') return t('activity.units', n)
    if (row.area === 'assets') return t('activity.devices', n)
    return t('activity.positions', n)
  }

  /** "Handed out · 3 positions"; a single allocation names the device: "Allocated · NB-0012 · …" */
  const summary = (row: Activity): string =>
    [
      enumLabel('activityKind', row.kind),
      ALLOCATION_KINDS.has(row.kind) ? row.detail : quantity(row),
    ]
      .filter(Boolean)
      .join(' · ')

  return { quantity, summary }
}
