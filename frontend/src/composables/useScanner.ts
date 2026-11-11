import { onBeforeUnmount, onMounted } from 'vue'

interface Scanner {
  onScan: (code: string) => void
  minLength: number
  maxGap: number
}

/** Mounted scanners; the last one (e.g. the page's own) gets the scans, not the top bar's. */
const scanners: Scanner[] = []
let buffer = ''
let last = 0

function handler(event: KeyboardEvent) {
  const scanner = scanners.at(-1)
  if (!scanner) return
  const target = event.target as HTMLElement | null
  if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return
  if (target?.isContentEditable) return

  const now = performance.now()
  if (now - last > scanner.maxGap) buffer = ''
  last = now

  if (event.key === 'Enter') {
    if (buffer.length >= scanner.minLength) {
      event.preventDefault()
      scanner.onScan(buffer)
    }
    buffer = ''
  } else if (event.key.length === 1) {
    buffer += event.key
  }
}

/**
 * Detect input from keyboard-wedge barcode scanners anywhere on the page.
 *
 * Scanners "type" very fast and finish with Enter. Keystrokes arriving less than
 * `maxGap` ms apart are collected; if at least `minLength` characters arrive
 * before Enter, `onScan` is called. Input fields keep working normally. Only the
 * scanner mounted last receives scans: a page's own scan field takes over from the
 * one in the top bar while it is shown.
 */
export function useScanner(onScan: (code: string) => void, { minLength = 5, maxGap = 35 } = {}) {
  const scanner: Scanner = { onScan, minLength, maxGap }
  onMounted(() => {
    if (!scanners.length) window.addEventListener('keydown', handler)
    scanners.push(scanner)
  })
  onBeforeUnmount(() => {
    scanners.splice(scanners.indexOf(scanner), 1)
    if (!scanners.length) window.removeEventListener('keydown', handler)
  })
}
