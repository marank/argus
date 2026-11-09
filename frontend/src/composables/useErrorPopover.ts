import { shallowReactive } from 'vue'

/**
 * Errors shown as a red popover pointing at what they are about: the button that started a
 * failed action, the scan field of a code not found, or a form field the server refused. One
 * popover at a time, drawn by `ErrorPopover` in `App.vue`; without an element to point at it
 * falls back to a toast.
 *
 * Form fields carry their error as `data-field-error` (see `useFieldErrors`): the popover then
 * stays until the value changes, and hovering or focusing another refused field shows its error.
 */
export const errorPopover = shallowReactive({
  anchor: null as HTMLElement | null,
  message: '',
  /** Raised for each error, so the same error shown twice opens the popover again. */
  serial: 0,
})

/** Errors already shown at their form fields, so `useAction` does not show them again. */
const shownAtFields = new WeakSet<object>()

export function markShownAtFields(error: unknown) {
  if (error && typeof error === 'object') shownAtFields.add(error)
}

export function wasShownAtFields(error: unknown): boolean {
  return !!error && typeof error === 'object' && shownAtFields.has(error)
}

/** The focused element, e.g. the button just clicked; `null` when nothing is focused. */
export function focusedElement(): HTMLElement | null {
  const active = document.activeElement
  return active instanceof HTMLElement && active !== document.body ? active : null
}

/** Shows `message` at `anchor` (default: the focused element). */
export function showError(message: string, anchor: Element | null = focusedElement()) {
  errorPopover.anchor = anchor instanceof HTMLElement ? anchor : null
  errorPopover.message = message
  errorPopover.serial++
}

export function hideError() {
  errorPopover.anchor = null
  errorPopover.message = ''
}

/** Shows the error of the first refused field inside `root` (default: the whole page). */
export function showFirstFieldError(root: ParentNode = document) {
  const field = root.querySelector<HTMLElement>('[data-field-error]')
  if (field) showError(field.dataset.fieldError ?? '', field)
}
