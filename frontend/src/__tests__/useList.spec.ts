import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent } from 'vue'
import { createI18n } from 'vue-i18n'

import { useList } from '@/composables/useList'
import { useLiveStore } from '@/stores/live'
import type { ListParams, Page } from '@/types/common'

/** Answers that the test resolves by hand, in any order. */
function controlledFetcher() {
  const pending: ((page: Page<string>) => void)[] = []
  const fetcher = vi.fn<(params: ListParams) => Promise<Page<string>>>(
    () => new Promise((resolve) => pending.push(resolve)),
  )
  const answer = (index: number, items: string[]) => pending[index]!({ items, count: items.length })
  return { fetcher, answer }
}

class FakeEventSource {
  static last: FakeEventSource
  static CLOSED = 2
  readyState = 1
  onopen: (() => void) | null = null
  onmessage: ((message: { data: string }) => void) | null = null
  onerror: (() => void) | null = null
  constructor() {
    FakeEventSource.last = this
  }
  addEventListener() {}
  close() {}
}

function mountList(fetcher: (params: ListParams) => Promise<Page<string>>) {
  let list!: ReturnType<typeof useList<string>>
  mount(
    defineComponent({
      setup() {
        list = useList(fetcher, { live: ['order'] })
        return () => null
      },
    }),
    { global: { plugins: [createI18n({ legacy: false, locale: 'en', missingWarn: false })] } },
  )
  return list
}

describe('useList', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.stubGlobal('EventSource', FakeEventSource)
    setActivePinia(createPinia())
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.unstubAllGlobals()
  })

  it('keeps the rows without a loading state on live updates', async () => {
    const { fetcher, answer } = controlledFetcher()
    const list = mountList(fetcher)
    list.load()
    answer(0, ['a'])
    await flushPromises()

    useLiveStore().start()
    FakeEventSource.last.onmessage?.({ data: JSON.stringify({ topic: 'order', id: 'o1' }) })
    await vi.advanceTimersByTimeAsync(500)
    expect(fetcher).toHaveBeenCalledTimes(2)
    expect(list.loading.value).toBe(false)
    expect(list.rows.value).toEqual(['a'])

    answer(1, ['a', 'b'])
    await flushPromises()
    expect(list.rows.value).toEqual(['a', 'b'])
  })

  it('drops an older answer that arrives after a newer one', async () => {
    const { fetcher, answer } = controlledFetcher()
    const list = mountList(fetcher)
    list.load()
    list.load()
    answer(1, ['new'])
    await flushPromises()
    answer(0, ['old'])
    await flushPromises()
    expect(list.rows.value).toEqual(['new'])
    expect(list.loading.value).toBe(false)
  })
})
