import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, ref } from 'vue'

import { useSegmentedDateInput } from '@/composables/useSegmentedDateInput'

const FORMAT = 'dd.MM.yyyy'

/** A date picker stand-in: one input, or two for a range. */
function picker(values: string[]) {
  const wrapper = mount(
    defineComponent({
      setup() {
        const root = ref<HTMLElement | null>(null)
        useSegmentedDateInput(root, () => FORMAT)
        return () =>
          h(
            'div',
            { ref: root },
            values.map((value) => h('input', { value })),
          )
      },
    }),
    { attachTo: document.body },
  )
  const inputs = wrapper.findAll('input').map((w) => w.element)
  const typed: string[] = []
  inputs.forEach((input) => input.addEventListener('input', () => typed.push(input.value)))
  return { wrapper, inputs, typed }
}

function key(input: HTMLInputElement, name: string, init: KeyboardEventInit = {}) {
  const event = new KeyboardEvent('keydown', {
    key: name,
    bubbles: true,
    cancelable: true,
    ...init,
  })
  input.dispatchEvent(event)
  return event
}

function type(input: HTMLInputElement, keys: string) {
  for (const k of keys) key(input, k)
}

const selection = (input: HTMLInputElement) => [input.selectionStart, input.selectionEnd]

describe('useSegmentedDateInput', () => {
  let mounted: { unmount: () => void } | null = null
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date(2026, 9, 20, 12, 0))
  })
  afterEach(() => {
    mounted?.unmount()
    mounted = null
    vi.useRealTimers()
  })

  function setup(values: string[]) {
    const result = picker(values)
    mounted = result.wrapper
    return result
  }

  it('selects the first part when tabbing in', () => {
    const { inputs } = setup(['20.10.2026'])
    inputs[0]!.focus()
    expect(selection(inputs[0]!)).toEqual([0, 2])
  })

  it('overwrites the day and moves on to the month', () => {
    const { inputs, typed } = setup(['20.10.2026'])
    inputs[0]!.focus()
    type(inputs[0]!, '05')
    expect(inputs[0]!.value).toBe('05.10.2026')
    expect(typed.at(-1)).toBe('05.10.2026')
    expect(selection(inputs[0]!)).toEqual([3, 5])
  })

  it('completes a digit that cannot start a two-digit day at once', () => {
    const { inputs } = setup(['20.10.2026'])
    inputs[0]!.focus()
    type(inputs[0]!, '4')
    expect(inputs[0]!.value).toBe('04.10.2026')
    expect(selection(inputs[0]!)).toEqual([3, 5])
  })

  it('waits for all four year digits before the picker reads it', () => {
    const { inputs, typed } = setup(['20.10.2026'])
    inputs[0]!.focus()
    key(inputs[0]!, 'End')
    type(inputs[0]!, '20')
    expect(inputs[0]!.value).toBe('20.10.0020')
    expect(typed).toEqual([])
    type(inputs[0]!, '27')
    expect(typed).toEqual(['20.10.2027'])
  })

  it('starts a segment afresh after a pause', () => {
    const { inputs } = setup(['20.10.2026'])
    inputs[0]!.focus()
    type(inputs[0]!, '1')
    vi.advanceTimersByTime(2000)
    type(inputs[0]!, '2')
    expect(inputs[0]!.value).toBe('02.10.2026')
  })

  it('steps the part with the arrow keys, by ten with Shift', () => {
    const { inputs } = setup(['20.10.2026'])
    inputs[0]!.focus()
    key(inputs[0]!, 'ArrowRight')
    const up = key(inputs[0]!, 'ArrowUp')
    expect(up.defaultPrevented).toBe(true)
    expect(inputs[0]!.value).toBe('20.11.2026')
    key(inputs[0]!, 'ArrowDown', { shiftKey: true })
    expect(inputs[0]!.value).toBe('20.01.2026')
    expect(selection(inputs[0]!)).toEqual([3, 5])
  })

  it('starts an empty field from today', () => {
    const { inputs } = setup([''])
    inputs[0]!.focus()
    key(inputs[0]!, 'ArrowUp')
    expect(inputs[0]!.value).toBe('21.10.2026')
  })

  it('moves between parts with arrows, separators, Home and End', () => {
    const { inputs } = setup(['20.10.2026'])
    const input = inputs[0]!
    input.focus()
    key(input, '.')
    expect(selection(input)).toEqual([3, 5])
    key(input, 'End')
    expect(selection(input)).toEqual([6, 10])
    key(input, 'ArrowLeft')
    expect(selection(input)).toEqual([3, 5])
    key(input, 'Home')
    expect(selection(input)).toEqual([0, 2])
    // The first part stays selected at the start of a single field.
    key(input, 'ArrowLeft')
    expect(selection(input)).toEqual([0, 2])
  })

  it('continues in the end date of a range and back', () => {
    const { inputs } = setup(['20.10.2026', '24.10.2026'])
    const [start, end] = inputs as [HTMLInputElement, HTMLInputElement]
    start.focus()
    key(start, 'End')
    key(start, 'ArrowRight')
    expect(document.activeElement).toBe(end)
    expect(selection(end)).toEqual([0, 2])
    key(end, 'ArrowLeft')
    expect(document.activeElement).toBe(start)
    expect(selection(start)).toEqual([6, 10])
  })

  it('starts an empty end date from the start date', () => {
    const { inputs } = setup(['20.10.2026', ''])
    const end = inputs[1]!
    end.focus()
    key(end, 'ArrowUp')
    expect(end.value).toBe('21.10.2026')
  })

  it('swallows letters but leaves shortcuts and Tab alone', () => {
    const { inputs } = setup(['20.10.2026'])
    const input = inputs[0]!
    input.focus()
    expect(key(input, 'x').defaultPrevented).toBe(true)
    expect(key(input, 'a', { ctrlKey: true }).defaultPrevented).toBe(false)
    expect(key(input, 'Tab').defaultPrevented).toBe(false)
    expect(input.value).toBe('20.10.2026')
  })

  it('keeps Backspace from breaking the format unless all is selected', () => {
    const { inputs } = setup(['20.10.2026'])
    const input = inputs[0]!
    input.focus()
    expect(key(input, 'Backspace').defaultPrevented).toBe(true)
    input.setSelectionRange(0, input.value.length)
    expect(key(input, 'Backspace').defaultPrevented).toBe(false)
  })

  it('selects the part under the caret on click', () => {
    const { inputs } = setup(['20.10.2026'])
    const input = inputs[0]!
    input.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
    input.focus()
    input.setSelectionRange(7, 7)
    input.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }))
    expect(selection(input)).toEqual([6, 10])
  })

  it('keeps a selection made by dragging', () => {
    const { inputs } = setup(['20.10.2026'])
    const input = inputs[0]!
    input.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }))
    input.focus()
    input.setSelectionRange(1, 8)
    input.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }))
    expect(selection(input)).toEqual([1, 8])
  })

  it('takes text without key events through the same logic', () => {
    const { inputs } = setup(['20.10.2026'])
    const input = inputs[0]!
    input.focus()
    const event = new InputEvent('beforeinput', {
      inputType: 'insertText',
      data: '5.3',
      bubbles: true,
      cancelable: true,
    })
    input.dispatchEvent(event)
    expect(event.defaultPrevented).toBe(true)
    // 5 completes the day; the dot moves on to the year, where 3 starts.
    expect(input.value).toBe('05.10.0003')
  })

  it('blocks deleting part of the text without key events', () => {
    const { inputs } = setup(['20.10.2026'])
    const input = inputs[0]!
    input.focus()
    const event = new InputEvent('beforeinput', {
      inputType: 'deleteContentBackward',
      bubbles: true,
      cancelable: true,
    })
    input.dispatchEvent(event)
    expect(event.defaultPrevented).toBe(true)
  })

  it('stops handling keys when unmounted', () => {
    const { wrapper, inputs } = picker(['20.10.2026'])
    const input = inputs[0]!
    input.focus()
    wrapper.unmount()
    expect(key(input, '5').defaultPrevented).toBe(false)
  })
})
