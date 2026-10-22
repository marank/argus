import { mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, ref, type Ref } from 'vue'

import { useLive } from '@/composables/useLive'
import { useLiveStore } from '@/stores/live'

/** Stands in for the browser's EventSource; the test plays the server. */
class FakeEventSource {
  static CLOSED = 2
  static last: FakeEventSource
  readyState = 1
  onopen: (() => void) | null = null
  onmessage: ((message: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  listeners: Record<string, () => void> = {}
  constructor(public url: string) {
    FakeEventSource.last = this
  }
  addEventListener(name: string, listener: () => void) {
    this.listeners[name] = listener
  }
  close() {}
  send(topic: string, id: string | null = null) {
    this.onmessage?.({ data: JSON.stringify({ topic, id }) })
  }
}

function setup(topics: string[], options: { id?: string; paused?: Ref<boolean> } = {}) {
  const reload = vi.fn<() => void>()
  mount(
    defineComponent({
      setup() {
        useLive(topics, reload, {
          id: options.id ? () => options.id : undefined,
          paused: options.paused ? () => options.paused!.value : undefined,
        })
        return () => null
      },
    }),
  )
  const live = useLiveStore()
  live.start()
  const source = FakeEventSource.last
  source.onopen?.()
  return { reload, source, live }
}

describe('useLive', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.stubGlobal('EventSource', FakeEventSource)
    setActivePinia(createPinia())
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('reloads once for a burst of matching signals', async () => {
    const { reload, source } = setup(['request'])
    source.send('request', 'r1')
    source.send('request', 'r2')
    source.send('order', 'o1')
    await vi.advanceTimersByTimeAsync(500)
    expect(reload).toHaveBeenCalledOnce()
  })

  it('skips a garbled frame and keeps listening', async () => {
    const { reload, source } = setup(['request'])
    expect(() => source.onmessage?.({ data: 'not json' })).not.toThrow()
    source.send('request', 'r1')
    await vi.advanceTimersByTimeAsync(500)
    expect(reload).toHaveBeenCalledOnce()
  })

  it('only counts signals for its own object', async () => {
    const { reload, source } = setup(['request'], { id: 'r1' })
    source.send('request', 'r2')
    await vi.advanceTimersByTimeAsync(500)
    expect(reload).not.toHaveBeenCalled()
    source.send('request', 'r1')
    await vi.advanceTimersByTimeAsync(500)
    expect(reload).toHaveBeenCalledOnce()
  })

  it('holds signals back while paused and reloads once afterwards', async () => {
    const paused = ref(true)
    const { reload, source } = setup(['issue'], { paused })
    source.send('issue', 'i1')
    await vi.advanceTimersByTimeAsync(500)
    expect(reload).not.toHaveBeenCalled()
    paused.value = false
    await vi.advanceTimersByTimeAsync(0)
    expect(reload).toHaveBeenCalledOnce()
  })

  it('reloads everything after a lost connection, but not after a planned end', async () => {
    const { reload, source, live } = setup(['order'])
    source.listeners.bye!()
    source.onerror?.()
    source.onopen?.()
    await vi.advanceTimersByTimeAsync(500)
    expect(reload).not.toHaveBeenCalled()

    source.onerror?.()
    expect(live.connected).toBe(false)
    source.onopen?.()
    await vi.advanceTimersByTimeAsync(500)
    expect(reload).toHaveBeenCalledOnce()
  })
})
