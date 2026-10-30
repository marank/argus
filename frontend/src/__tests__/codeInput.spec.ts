import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { defineComponent, h, ref } from 'vue'

import CodeInput from '@/components/common/CodeInput.vue'

function setup(initial = '', length = 6) {
  const code = ref(initial)
  const completed: string[] = []
  const wrapper = mount(
    defineComponent({
      setup: () => () =>
        h(CodeInput, {
          modelValue: code.value,
          'onUpdate:modelValue': (value: string) => (code.value = value),
          onComplete: (value: string) => completed.push(value),
          length,
          label: 'Code',
        }),
    }),
    { attachTo: document.body },
  )
  const boxes = () => wrapper.findAll('input').map((w) => w.element)
  return { code, completed, wrapper, boxes }
}

function typeDigit(box: HTMLInputElement, data: string) {
  box.value = data
  box.dispatchEvent(new InputEvent('input', { data }))
}

function key(box: HTMLInputElement, name: string) {
  const event = new KeyboardEvent('keydown', { key: name, cancelable: true })
  box.dispatchEvent(event)
  return event
}

function paste(box: HTMLInputElement, text: string) {
  const event = new Event('paste', { cancelable: true }) as Event & {
    clipboardData: { getData: () => string }
  }
  event.clipboardData = { getData: () => text }
  box.dispatchEvent(event)
  return event
}

describe('CodeInput', () => {
  let unmount: (() => void) | null = null
  afterEach(() => {
    unmount?.()
    unmount = null
  })
  function mounted(...args: Parameters<typeof setup>) {
    const result = setup(...args)
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('shows one labelled box per digit', () => {
    const { boxes } = mounted('12')
    expect(boxes()).toHaveLength(6)
    expect(boxes().map((b) => b.value)).toEqual(['1', '2', '', '', '', ''])
    expect(boxes()[2]!.getAttribute('aria-label')).toBe('Code 3/6')
  })

  it('moves on with each typed digit and completes', () => {
    const { code, completed, boxes } = mounted()
    for (const [index, digit] of [...'123456'].entries()) typeDigit(boxes()[index]!, digit)
    expect(code.value).toBe('123456')
    expect(completed).toEqual(['123456'])
  })

  it('focuses the next box after a digit', () => {
    const { boxes } = mounted()
    typeDigit(boxes()[0]!, '7')
    expect(document.activeElement).toBe(boxes()[1])
  })

  it('ignores letters', () => {
    const { code, boxes } = mounted()
    typeDigit(boxes()[0]!, 'a')
    expect(code.value).toBe('')
    expect(boxes()[0]!.value).toBe('')
  })

  it('keeps the code contiguous when a later box is typed into', () => {
    const { code, boxes } = mounted('1')
    typeDigit(boxes()[3]!, '9')
    expect(code.value).toBe('1')
  })

  it('spreads a pasted code over all boxes', () => {
    const { code, completed, boxes } = mounted()
    const event = paste(boxes()[3]!, '987 654')
    expect(event.defaultPrevented).toBe(true)
    expect(code.value).toBe('987654')
    expect(completed).toEqual(['987654'])
  })

  it('takes autofill without input data', () => {
    const { code, boxes } = mounted()
    const box = boxes()[0]!
    box.value = '246810'
    box.dispatchEvent(new Event('input'))
    expect(code.value).toBe('246810')
  })

  it('deletes backwards with Backspace', () => {
    const { code, boxes } = mounted('123')
    // On the empty box after the digits: the previous digit goes.
    expect(key(boxes()[3]!, 'Backspace').defaultPrevented).toBe(true)
    expect(code.value).toBe('12')
    // On a filled box: that digit and the ones after it go.
    key(boxes()[0]!, 'Backspace')
    expect(code.value).toBe('')
    key(boxes()[0]!, 'Backspace')
    expect(code.value).toBe('')
  })

  it('moves between boxes with the arrow keys, not past the typed digits', () => {
    const { boxes } = mounted('12')
    key(boxes()[1]!, 'ArrowLeft')
    expect(document.activeElement).toBe(boxes()[0])
    key(boxes()[1]!, 'ArrowRight')
    expect(document.activeElement).toBe(boxes()[2])
    key(boxes()[2]!, 'ArrowRight')
    expect(document.activeElement).toBe(boxes()[2])
  })

  it('lands on the next free box when clicking further right', () => {
    const { boxes } = mounted('1')
    boxes()[5]!.focus()
    expect(document.activeElement).toBe(boxes()[1])
  })

  it('follows a code set from outside', async () => {
    const { code, boxes, wrapper } = mounted('12')
    code.value = ''
    await wrapper.vm.$nextTick()
    expect(boxes().map((b) => b.value)).toEqual(['', '', '', '', '', ''])
  })
})
