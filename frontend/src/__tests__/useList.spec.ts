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

function mountList(
  fetcher: (params: ListParams) => Promise<Page<string>>,
  options: Parameters<typeof useList<string>>[1] = { live: ['order'] },
) {
  let list!: ReturnType<typeof useList<string>>
  mount(
    defineComponent({
      setup() {
        list = useList(fetcher, options)
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

  describe('parameters', () => {
    const answering = () =>
      vi.fn<(params: ListParams) => Promise<Page<string>>>(async () => ({
        items: ['x'],
        count: 60,
      }))
    const goTo = (list: ReturnType<typeof mountList>, page: number) =>
      (list.pagination.value.onUpdatePage as (page: number) => void)(page)
    const lastParams = (fetcher: ReturnType<typeof answering>) => fetcher.mock.lastCall![0]

    it('asks for the first page with the defaults', async () => {
      const fetcher = answering()
      const list = mountList(fetcher, { pageSize: 50, ordering: 'name', filters: { kind: 'a' } })
      await list.load()
      expect(lastParams(fetcher)).toEqual({
        page: 1,
        page_size: 50,
        q: undefined,
        ordering: 'name',
        kind: 'a',
      })
      expect(list.count.value).toBe(60)
      expect(list.pagination.value.itemCount).toBe(60)
    })

    it('searches after a pause in typing, from the first page', async () => {
      const fetcher = answering()
      const list = mountList(fetcher)
      goTo(list, 3)
      list.search.value = 'lap'
      await vi.advanceTimersByTimeAsync(100)
      list.search.value = 'laptop'
      await vi.advanceTimersByTimeAsync(250)
      expect(fetcher).toHaveBeenCalledTimes(2)
      expect(lastParams(fetcher)).toMatchObject({ q: 'laptop', page: 1 })
    })

    it('reloads from the first page when a filter changes', async () => {
      const fetcher = answering()
      const list = mountList(fetcher, { filters: { status: null } })
      goTo(list, 2)
      expect(lastParams(fetcher).page).toBe(2)
      list.filters.status = 'open'
      await flushPromises()
      expect(lastParams(fetcher)).toMatchObject({ status: 'open', page: 1 })
    })

    it('changes the page size and starts on the first page', async () => {
      const fetcher = answering()
      const list = mountList(fetcher)
      const setPageSize = list.pagination.value.onUpdatePageSize as (size: number) => void
      goTo(list, 2)
      setPageSize(100)
      expect(lastParams(fetcher)).toMatchObject({ page: 1, page_size: 100 })
    })

    it('sorts by the column, descending with a minus, back to the default without', () => {
      const fetcher = answering()
      const list = mountList(fetcher, { ordering: 'name' })
      list.onSort({ columnKey: 'price', order: 'descend', sorter: true })
      expect(lastParams(fetcher).ordering).toBe('-price')
      list.onSort([{ columnKey: 'price', order: 'ascend', sorter: true }])
      expect(lastParams(fetcher).ordering).toBe('price')
      list.onSort({ columnKey: 'price', order: false, sorter: true })
      expect(lastParams(fetcher).ordering).toBe('name')
      list.onSort(null)
      expect(lastParams(fetcher).ordering).toBe('name')
    })

    it('keeps rows grouped before the user sort', () => {
      const fetcher = answering()
      const list = mountList(fetcher, { groupOrdering: () => 'category__name' })
      list.load()
      expect(lastParams(fetcher).ordering).toBe('category__name')
      list.onSort({ columnKey: 'name', order: 'ascend', sorter: true })
      expect(lastParams(fetcher).ordering).toBe('category__name,name')
    })

    it('ends the loading state when the request fails', async () => {
      const list = mountList(async () => {
        throw new Error('offline')
      })
      await expect(list.load()).rejects.toThrow('offline')
      expect(list.loading.value).toBe(false)
    })
  })
})
