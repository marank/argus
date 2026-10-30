/**
 * Finding and using what a user sees on a mounted page. Naive UI teleports modals and
 * popups to the end of the body and keeps closed ones there with `display: none`, so
 * only shown elements count, and the last match is the one on top.
 */
import { flushPromises } from '@vue/test-utils'

export function shown(element: Element): boolean {
  for (let el: Element | null = element; el; el = el.parentElement)
    if ((el as HTMLElement).style?.display === 'none') return false
  return true
}

/** A button's visible label, without a keyboard hint (`<kbd>`). */
const label = (b: HTMLButtonElement) =>
  (b.textContent ?? '').replace(b.querySelector('kbd')?.textContent ?? '', '').trim()

/** Shown buttons labelled `text`, or titled so (icon buttons). */
export const buttons = (text: string, within: ParentNode = document.body) =>
  [...within.querySelectorAll('button')].filter(
    (b) => (label(b) === text || b.title === text) && shown(b),
  )

export function button(text: string, within: ParentNode = document.body): HTMLButtonElement {
  const found = buttons(text, within)
  if (!found.length) throw new Error(`no button "${text}"`)
  return found.at(-1)!
}

export const hasButton = (text: string, within: ParentNode = document.body) =>
  buttons(text, within).length > 0

export async function click(target: string | Element) {
  ;(typeof target === 'string' ? button(target) : (target as HTMLElement)).click()
  await flushPromises()
}

/** Types into a plain or Naive UI input as a user would. */
export async function typeInto(element: Element | null | undefined, value: string) {
  if (!element) throw new Error('no input')
  const input = element as HTMLInputElement | HTMLTextAreaElement
  input.value = value
  input.dispatchEvent(new Event('input'))
  await flushPromises()
}
