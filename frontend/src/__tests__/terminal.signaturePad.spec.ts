import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import SignaturePad from '@/components/terminal/SignaturePad.vue'
import { i18n } from '@/i18n'

import { drawOn, SIGNATURE, stubCanvas } from './portalHelpers'

function mountPad() {
  return mount(SignaturePad, { attachTo: document.body, global: { plugins: [i18n] } })
}

describe('SignaturePad', () => {
  // jsdom cannot draw: the stub accepts the drawing calls and exports a fixed PNG.
  beforeEach(stubCanvas)
  afterEach(() => {
    document.body.innerHTML = ''
    vi.restoreAllMocks()
  })

  it('starts empty and asks for a signature', () => {
    const pad = mountPad()
    expect(pad.text()).toContain('Sign here')
    expect(pad.emitted('change')).toEqual([[true]])
    expect(pad.vm.isEmpty()).toBe(true)
    pad.unmount()
  })

  it('reports a stroke as signed and exports it as a PNG data URL', async () => {
    const pad = mountPad()
    await drawOn(pad.find('canvas').element)
    expect(pad.emitted('change')!.at(-1)).toEqual([false])
    expect(pad.vm.isEmpty()).toBe(false)
    expect(pad.text()).not.toContain('Sign here')
    expect(pad.vm.toDataUrl()).toBe(SIGNATURE)
    expect(HTMLCanvasElement.prototype.toDataURL).toHaveBeenCalledWith('image/png')
    pad.unmount()
  })

  it('reports signing only once per signature', async () => {
    const pad = mountPad()
    await drawOn(pad.find('canvas').element)
    await drawOn(pad.find('canvas').element)
    expect(pad.emitted('change')).toEqual([[true], [false]])
    pad.unmount()
  })

  it('clears the signature to start over', async () => {
    const pad = mountPad()
    await drawOn(pad.find('canvas').element)
    await pad.find('button.clear').trigger('click')
    expect(pad.emitted('change')!.at(-1)).toEqual([true])
    expect(pad.vm.isEmpty()).toBe(true)
    expect(pad.text()).toContain('Sign here')
    pad.unmount()
  })

  it('does not draw when the pointer only passes over the pad', async () => {
    const pad = mountPad()
    const canvas = pad.find('canvas').element
    canvas.dispatchEvent(new MouseEvent('pointermove', { clientX: 5, clientY: 5 }))
    await flushPromises()
    expect(pad.emitted('change')).toEqual([[true]])
    // After lifting the pen, moving on does not continue the line either.
    await drawOn(canvas)
    await pad.find('button.clear').trigger('click')
    canvas.dispatchEvent(new MouseEvent('pointermove', { clientX: 50, clientY: 5 }))
    await flushPromises()
    expect(pad.vm.isEmpty()).toBe(true)
    pad.unmount()
  })
})
