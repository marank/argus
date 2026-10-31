import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import AppLayout from '@/layouts/AppLayout.vue'

import { click } from './dom'
import { mountView } from './layoutHelpers'

vi.mock('@/stores/live', () => ({
  useLiveStore: () => ({
    start: () => undefined,
    stop: () => undefined,
    subscribe: () => () => undefined,
    connected: false,
  }),
}))
vi.mock('@/api/notifications', () => ({
  notificationsApi: {
    list: async () => ({ items: [], count: 0 }),
    unread: async () => ({ unread: 0 }),
  },
}))

/** Pretends a screen of the given width for the layout's media queries. */
function screenWidth(width: number) {
  window.matchMedia = ((query: string) => {
    const max = /max-width:\s*([\d.]+)px/.exec(query)
    const min = /min-width:\s*([\d.]+)px/.exec(query)
    return {
      matches: (!max || width <= Number(max[1])) && (!min || width >= Number(min[1])),
      media: query,
      addEventListener: () => undefined,
      removeEventListener: () => undefined,
    }
  }) as unknown as typeof window.matchMedia
}

describe('AppLayout', () => {
  const original = window.matchMedia
  let unmount: (() => void) | null = null
  afterEach(() => {
    unmount?.()
    unmount = null
    window.matchMedia = original
    document.body.innerHTML = ''
    localStorage.clear()
  })

  async function show(width: number) {
    screenWidth(width)
    const result = await mountView(AppLayout)
    unmount = () => result.wrapper.unmount()
    return result
  }

  beforeEach(() => localStorage.clear())

  it('keeps the sidebar on a wide screen', async () => {
    await show(1400)
    expect(document.body.querySelector('.n-layout-sider')).not.toBeNull()
    expect(document.body.querySelector('[title="Menu"]')).toBeNull()
  })

  it('has no sidebar on a phone; the menu slides in and closes on the way to a page', async () => {
    const { router } = await show(375)
    expect(document.body.querySelector('.n-layout-sider')).toBeNull()
    expect(document.body.querySelector('.sidebar')).toBeNull()

    await click(document.body.querySelector<HTMLElement>('[title="Menu"]')!)
    expect(document.body.querySelector('.n-drawer .sidebar')).not.toBeNull()

    await router.push('/portal/new')
    await flushPromises()
    // Naive UI keeps the closed drawer in the page, hidden.
    expect(document.body.querySelector<HTMLElement>('.n-drawer')?.style.display).toBe('none')
  })
})
