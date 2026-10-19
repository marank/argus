import { onBeforeUnmount, onMounted } from 'vue'

/**
 * Detect input from keyboard-wedge barcode scanners anywhere on the page.
 *
 * Scanners "type" very fast and finish with Enter. Keystrokes arriving less than
 * `maxGap` ms apart are collected; if at least `minLength` characters arrive
 * before Enter, `onScan` is called. Input fields keep working normally.
 */
export function useScanner(onScan: (code: string) => void, { minLength = 5, maxGap = 35 } = {}) {
  let buffer = ''
  let last = 0

  function handler(event: KeyboardEvent) {
    const target = event.target as HTMLElement | null
    if (target && ['INPUT', 'TEXTAREA', 'SELECT'].includes(target.tagName)) return
    if (target?.isContentEditable) return

    const now = performance.now()
    if (now - last > maxGap) buffer = ''
    last = now

    if (event.key === 'Enter') {
      if (buffer.length >= minLength) {
        event.preventDefault()
        onScan(buffer)
      }
      buffer = ''
    } else if (event.key.length === 1) {
      buffer += event.key
    }
  }

  onMounted(() => window.addEventListener('keydown', handler))
  onBeforeUnmount(() => window.removeEventListener('keydown', handler))
}
