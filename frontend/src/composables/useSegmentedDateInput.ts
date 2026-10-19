import { onBeforeUnmount, onMounted, type Ref } from 'vue'

import {
  formatParts,
  parseFormat,
  partsFromDate,
  readParts,
  segmentAt,
  step,
  typeDigit,
  type SegmentKind,
} from '@/utils/dateSegments'

interface InputState {
  segment: number
  buffer: string
  at: number
}

const BUFFER_TIMEOUT = 1500
const SEPARATORS = new Set(['.', '/', '-', ':', ' ', ','])

/**
 * Native-like editing for the text inputs inside a date picker (one input, or two
 * for ranges): clicking selects the day/month/year/… under the caret, digits
 * overwrite that part and move on when complete, arrow keys step it or move
 * between parts (and between start and end of a range).
 *
 * The picker still owns parsing: after each change an `input` event is dispatched
 * so it reads the new text exactly as if it had been typed.
 */
export function useSegmentedDateInput(root: Ref<HTMLElement | null>, format: () => string) {
  const state = new WeakMap<HTMLInputElement, InputState>()

  const inputs = () => [...(root.value?.querySelectorAll('input') ?? [])]
  const segments = () => parseFormat(format())
  const stateOf = (input: HTMLInputElement) => {
    let s = state.get(input)
    if (!s) state.set(input, (s = { segment: 0, buffer: '', at: 0 }))
    return s
  }

  function select(input: HTMLInputElement, index: number) {
    const segment = segments()[index]
    if (!segment) return
    stateOf(input).segment = index
    const apply = () => {
      if (document.activeElement === input) input.setSelectionRange(segment.start, segment.end)
    }
    apply()
    // The picker re-renders the input after each change and moves the caret to the
    // end, so apply the selection again once that has happened.
    requestAnimationFrame(() => requestAnimationFrame(apply))
  }

  function currentParts(input: HTMLInputElement) {
    const own = readParts(input.value, format())
    if (own) return own
    // An empty end date starts from the start date; anything else from today.
    const [first] = inputs()
    const fromStart = first && first !== input ? readParts(first.value, format()) : null
    return fromStart ?? partsFromDate(new Date())
  }

  function write(input: HTMLInputElement, parts: Record<SegmentKind, number>, dispatch = true) {
    input.value = formatParts(format(), parts)
    if (dispatch) input.dispatchEvent(new Event('input', { bubbles: true }))
  }

  /** Move to another segment; past the edges, continue in the other range input. */
  function move(input: HTMLInputElement, index: number) {
    const count = segments().length
    const list = inputs()
    const position = list.indexOf(input)
    if (index >= count && position < list.length - 1) {
      const next = list[position + 1]!
      next.focus()
      select(next, 0)
    } else if (index < 0 && position > 0) {
      const previous = list[position - 1]!
      previous.focus()
      select(previous, count - 1)
    } else {
      select(input, Math.min(Math.max(index, 0), count - 1))
    }
  }

  function typeInto(input: HTMLInputElement, digit: string) {
    const s = stateOf(input)
    const all = segments()
    const index = Math.min(s.segment, all.length - 1)
    const kind = all[index]!.kind
    const fresh = Date.now() - s.at > BUFFER_TIMEOUT
    const result = typeDigit(currentParts(input), kind, fresh ? '' : s.buffer, digit)
    s.buffer = result.buffer
    s.at = Date.now()
    // A half-typed year ("0002") would be parsed as year 2, so wait for all digits.
    write(input, result.parts, !(kind === 'year' && !result.complete))
    if (result.complete) {
      s.buffer = ''
      move(input, index + 1)
    } else {
      select(input, index)
    }
  }

  /**
   * Text that arrives without key events (touch keyboards, IME, autofill tools)
   * goes through the same segment logic.
   */
  function onBeforeInput(event: InputEvent) {
    const input = event.target as HTMLInputElement
    if (!(input instanceof HTMLInputElement) || !inputs().includes(input)) return
    if (event.inputType === 'insertText' && event.data) {
      event.preventDefault()
      for (const char of event.data) {
        if (/\d/.test(char)) typeInto(input, char)
        else if (SEPARATORS.has(char)) move(input, stateOf(input).segment + 1)
      }
    } else if (event.inputType.startsWith('delete') && input.value) {
      const everything = input.selectionStart === 0 && input.selectionEnd === input.value.length
      if (!everything) {
        event.preventDefault()
        stateOf(input).buffer = ''
      }
    }
  }

  function onKeydown(event: KeyboardEvent) {
    const input = event.target as HTMLInputElement
    if (!(input instanceof HTMLInputElement) || !inputs().includes(input)) return
    if (event.ctrlKey || event.metaKey || event.altKey) return
    if (['Tab', 'Enter', 'Escape'].includes(event.key)) return

    const all = segments()
    const s = stateOf(input)
    const index = Math.min(s.segment, all.length - 1)
    const kind = all[index]!.kind
    const handled = () => {
      event.preventDefault()
      event.stopPropagation()
    }

    if (/^\d$/.test(event.key)) {
      handled()
      typeInto(input, event.key)
    } else if (event.key === 'ArrowUp' || event.key === 'ArrowDown') {
      handled()
      const delta = (event.key === 'ArrowUp' ? 1 : -1) * (event.shiftKey ? 10 : 1)
      s.buffer = ''
      write(input, step(currentParts(input), kind, delta))
      select(input, index)
    } else if (event.key === 'ArrowRight' || SEPARATORS.has(event.key)) {
      handled()
      s.buffer = ''
      move(input, index + 1)
    } else if (event.key === 'ArrowLeft') {
      handled()
      s.buffer = ''
      move(input, index - 1)
    } else if (event.key === 'Home' || event.key === 'End') {
      handled()
      select(input, event.key === 'Home' ? 0 : all.length - 1)
    } else if (event.key === 'Backspace' || event.key === 'Delete') {
      // Clearing the whole field (everything selected) stays possible.
      const everything = input.selectionStart === 0 && input.selectionEnd === input.value.length
      if (!everything || !input.value) {
        handled()
        s.buffer = ''
        select(input, index)
      }
    } else if (event.key.length === 1) {
      handled() // letters and other characters have no place in a date
    }
  }

  let pointerDown = false
  const onMouseDown = () => (pointerDown = true)

  function onMouseUp(event: MouseEvent) {
    pointerDown = false
    const input = event.target as HTMLInputElement
    if (!(input instanceof HTMLInputElement) || !inputs().includes(input)) return
    if (input.selectionStart !== input.selectionEnd || !input.value) return
    stateOf(input).buffer = ''
    select(input, segmentAt(segments(), input.selectionStart ?? 0))
  }

  function onFocusIn(event: FocusEvent) {
    const input = event.target as HTMLInputElement
    if (!(input instanceof HTMLInputElement) || !inputs().includes(input) || !input.value) return
    // Tabbing in selects the first part; for clicks, mouseup picks the part under the caret.
    if (!pointerDown) select(input, 0)
  }

  onMounted(() => {
    root.value?.addEventListener('keydown', onKeydown, true)
    root.value?.addEventListener('beforeinput', onBeforeInput as EventListener, true)
    root.value?.addEventListener('mousedown', onMouseDown)
    root.value?.addEventListener('mouseup', onMouseUp)
    root.value?.addEventListener('focusin', onFocusIn)
  })
  onBeforeUnmount(() => {
    root.value?.removeEventListener('keydown', onKeydown, true)
    root.value?.removeEventListener('beforeinput', onBeforeInput as EventListener, true)
    root.value?.removeEventListener('mousedown', onMouseDown)
    root.value?.removeEventListener('mouseup', onMouseUp)
    root.value?.removeEventListener('focusin', onFocusIn)
  })
}
