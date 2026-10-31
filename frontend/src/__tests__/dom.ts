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

/** What a screen reader calls a control: its aria-label, labelling element or `<label>`. */
function accessibleName(element: Element): string {
  const labelledBy = element.getAttribute('aria-labelledby')
  const name =
    element.getAttribute('aria-label') ??
    (labelledBy ? document.getElementById(labelledBy)?.textContent : null) ??
    element.closest('label')?.textContent
  return (name ?? '').trim()
}

/** The shown control of the given role (checkbox, switch, …) whose name starts with `name`. */
export function control(role: string, name: string, within: ParentNode = document.body) {
  const found = [...within.querySelectorAll<HTMLElement>(`[role="${role}"]`)].filter(
    (el) => accessibleName(el).startsWith(name) && shown(el),
  )
  if (!found.length) throw new Error(`no ${role} "${name}"`)
  return found.at(-1)!
}

/** The shown element matching `selector` (a table row by default) that mentions `text`. */
export function rowWith(text: string, within: ParentNode = document.body, selector = 'tr') {
  const found = [...within.querySelectorAll<HTMLElement>(selector)].find(
    (el) => el.textContent?.includes(text) && shown(el),
  )
  if (!found) throw new Error(`no ${selector} with "${text}"`)
  return found
}

/** The entries of the open dropdown menu. Naive UI gives them no role, hence its classes. */
export const menuEntries = () =>
  [...document.body.querySelectorAll('.n-dropdown-option')]
    .filter(shown)
    .map((option) => option.textContent?.trim())

/** Picks an entry of the open dropdown menu. */
export async function chooseMenuEntry(label: string) {
  const option = [...document.body.querySelectorAll('.n-dropdown-option')].find(
    (o) => o.textContent?.trim() === label && shown(o),
  )
  if (!option) throw new Error(`no menu entry "${label}"`)
  option.querySelector<HTMLElement>('.n-dropdown-option-body')!.click()
  await flushPromises()
}

/**
 * jsdom lacks matchMedia, which Naive UI and the layout ask. Without a width no query
 * matches; with one, `min-width` / `max-width` queries answer as on such a screen.
 * Returns a function that puts the previous matchMedia back.
 */
export function fakeMatchMedia(width?: number): () => void {
  const original = window.matchMedia
  window.matchMedia = (query: string) => {
    const max = /max-width:\s*([\d.]+)px/.exec(query)
    const min = /min-width:\s*([\d.]+)px/.exec(query)
    return {
      matches:
        width !== undefined &&
        (!max || width <= Number(max[1])) &&
        (!min || width >= Number(min[1])),
      media: query,
      onchange: null,
      addEventListener: () => {},
      removeEventListener: () => {},
      addListener: () => {},
      removeListener: () => {},
      dispatchEvent: () => false,
    } as MediaQueryList
  }
  return () => {
    window.matchMedia = original
  }
}
