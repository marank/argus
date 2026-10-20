/** Visual tone of status values, used by StatusTag. */
export type Tone = 'default' | 'info' | 'success' | 'warning' | 'error' | 'primary'

const TONES: Record<string, Record<string, Tone>> = {
  assetStatus: {
    in_stock: 'success',
    reserved: 'primary',
    in_use: 'info',
    in_repair: 'warning',
    lost: 'error',
    retired: 'default',
  },
  reservationStatus: {
    pending_approval: 'default',
    submitted: 'warning',
    confirmed: 'primary',
    ready: 'success',
    handed_out: 'info',
    completed: 'default',
    rejected: 'error',
    cancelled: 'default',
  },
  orderStatus: {
    draft: 'warning',
    ordered: 'info',
    partially_received: 'primary',
    received: 'success',
    cancelled: 'default',
  },
  condition: { new: 'success', good: 'info', worn: 'warning', defective: 'error' },
  issueStatus: { open: 'warning', in_progress: 'info', resolved: 'success' },
  approval: { pending: 'warning', approved: 'success', rejected: 'error' },
}

export function toneOf(group: string, value: string): Tone {
  return TONES[group]?.[value] ?? 'default'
}
