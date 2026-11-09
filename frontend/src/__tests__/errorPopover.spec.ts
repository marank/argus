import { flushPromises, mount } from '@vue/test-utils'
import { NMessageProvider } from 'naive-ui'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, nextTick } from 'vue'

import ErrorPopover from '@/components/common/ErrorPopover.vue'
import {
  errorPopover,
  hideError,
  showError,
  showFirstFieldError,
} from '@/composables/useErrorPopover'

import { errorPopoverText } from './dom'

describe('ErrorPopover', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    hideError()
    const wrapper = mount(
      defineComponent({
        render: () => h(NMessageProvider, null, { default: () => h(ErrorPopover) }),
      }),
      { attachTo: document.body },
    )
    unmount = () => wrapper.unmount()
  })
  afterEach(() => {
    unmount?.()
    document.body.innerHTML = ''
    vi.useRealTimers()
  })

  function element(html: string): HTMLElement {
    const host = document.createElement('div')
    host.innerHTML = html
    document.body.append(host)
    return host.firstElementChild as HTMLElement
  }
  const settle = async () => {
    await nextTick()
    await flushPromises()
  }
  const press = (key = 'a') => document.dispatchEvent(new KeyboardEvent('keydown', { key }))
  const pointerDown = (target: Element) =>
    target.dispatchEvent(new Event('pointerdown', { bubbles: true }))

  it('points at the button of a failed action and closes on a click elsewhere', async () => {
    const save = element('<button>Save</button>')
    showError('Already handed out.', save)
    await settle()
    expect(errorPopoverText()).toBe('Already handed out.')

    pointerDown(save)
    await settle()
    expect(errorPopover.message).toBe('Already handed out.')
    pointerDown(document.body)
    await settle()
    expect(errorPopover.message).toBe('')
    expect(errorPopoverText()).toBe('')
  })

  it('closes on a key press and after a while', async () => {
    const save = element('<button>Save</button>')
    showError('Nope.', save)
    await settle()
    press()
    expect(errorPopover.message).toBe('')

    vi.useFakeTimers()
    showError('Still nope.', save)
    await nextTick()
    vi.advanceTimersByTime(8000)
    expect(errorPopover.message).toBe('')
  })

  it('shows the error as a toast with nothing to point at', async () => {
    showError('Server not reachable.', null)
    await settle()
    expect(errorPopoverText()).toBe('')
    expect(document.body.querySelector('.n-message')?.textContent).toContain(
      'Server not reachable.',
    )
  })

  it('stays at a refused field until its error goes', async () => {
    const field = element('<div data-field-error="Taken."><div class="n-form-item-blank" /></div>')
    showFirstFieldError()
    await settle()
    expect(errorPopoverText()).toBe('Taken.')

    press()
    expect(errorPopover.message).toBe('Taken.')
    field.dataset.fieldError = 'Too long.'
    await settle()
    expect(errorPopover.message).toBe('Too long.')
    delete field.dataset.fieldError
    await settle()
    expect(errorPopover.message).toBe('')
  })

  it('shows the error of a refused field when it is hovered or focused', async () => {
    const first = element('<div data-field-error="Taken."><input></div>')
    const second = element('<div data-field-error="Required."><input></div>')
    showFirstFieldError()
    await settle()
    second.dispatchEvent(new Event('mouseover', { bubbles: true }))
    await settle()
    expect(errorPopoverText()).toBe('Required.')
    first.querySelector('input')!.dispatchEvent(new FocusEvent('focusin', { bubbles: true }))
    await settle()
    expect(errorPopoverText()).toBe('Taken.')
  })

  it('closes when the element it points at goes away', async () => {
    const save = element('<button>Save</button>')
    showError('Nope.', save)
    await settle()
    save.remove()
    await new Promise((resolve) => requestAnimationFrame(resolve))
    await settle()
    expect(errorPopover.message).toBe('')
  })

  it('defaults to the focused element', () => {
    const save = element('<button>Save</button>')
    save.focus()
    showError('Nope.')
    expect(errorPopover.anchor).toBe(save)
  })
})
