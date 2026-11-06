import { flushPromises, mount } from '@vue/test-utils'
import { NDialogProvider, NMessageProvider } from 'naive-ui'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'
import { CopyPlus } from '@lucide/vue'

import CrudPage from '@/components/crud/CrudPage.vue'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

import { makeUser } from './helpers'

interface Product {
  id: string
  name: string
  notes: string
  tags: { id: string; name: string }[]
  predecessor: { id: string; name: string } | null
}

const OLD: Product = {
  id: 'p1',
  name: 'Scanner 1',
  notes: 'Ask the warehouse',
  tags: [{ id: 't1', name: 'Rugged' }],
  predecessor: null,
}

/** A resource whose records can have a successor that takes over notes and tags. */
async function mountPage() {
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().user = makeUser({ is_it_staff: true, permissions: { models: 'write' } })
  const list = vi.fn<() => Promise<{ items: Product[]; count: number }>>(async () => ({
    items: [OLD],
    count: 1,
  }))
  const create = vi.fn<(data: object) => Promise<Product>>(
    async (data) => ({ ...OLD, id: 'p2', ...data }) as Product,
  )
  const resource = defineResource<Product>({
    key: 'models',
    permission: 'models',
    api: {
      list,
      create,
      update: vi.fn<(id: string, data: object) => Promise<Product>>(),
      remove: vi.fn<(id: string) => Promise<true>>(),
    },
    title: (p) => p.name,
    columns: [{ key: 'name', label: 'common.name' }],
    derive: {
      label: 'masterdata.createSuccessor',
      icon: CopyPlus,
      link: 'predecessor',
      copy: ['notes', 'tags'],
    },
    sections: [
      {
        fields: [
          { key: 'name', label: 'common.name', type: 'text', required: true },
          { key: 'notes', label: 'common.notes', type: 'textarea' },
          {
            key: 'tags',
            label: 'masterdata.fields.compatibleWith',
            type: 'entity',
            multiple: true,
            fetcher: async () => ({ items: [], count: 0 }),
            display: (t: { name: string }) => t.name,
            initial: (p: Product) => p.tags,
          },
          {
            key: 'predecessor',
            label: 'masterdata.fields.predecessor',
            type: 'entity',
            fetcher: list,
            display: (p: Product) => p.name,
            initial: (p: Product) => p.predecessor,
          },
        ],
      },
    ],
    defaults: () => ({ name: '', notes: '', tags: [], predecessor: null }),
    toForm: (p) => ({
      name: p.name,
      notes: p.notes,
      tags: p.tags.map((t) => t.id),
      predecessor: p.predecessor?.id ?? null,
    }),
  })
  const wrapper = mount(
    defineComponent({
      render: () =>
        h(NMessageProvider, null, {
          default: () => h(NDialogProvider, null, { default: () => h(CrudPage, { resource }) }),
        }),
    }),
    { attachTo: document.body, global: { plugins: [i18n, pinia] } },
  )
  await flushPromises()
  return { create, wrapper }
}

describe('CrudPage derive', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  })
  afterEach(() => {
    unmount?.()
    document.body.innerHTML = ''
    localStorage.clear()
    vi.restoreAllMocks()
  })

  it('creates a successor that takes over the shared fields and links the original', async () => {
    const { create, wrapper } = await mountPage()
    unmount = () => wrapper.unmount()
    document.body.querySelector<HTMLButtonElement>('button[aria-label="Create successor"]')!.click()
    await flushPromises()
    const form = document.body.querySelector('.ar-form')!
    expect(form.textContent).toContain('Scanner 1')
    expect(form.textContent).toContain('Rugged')
    expect(form.querySelector('textarea')!.value).toBe('Ask the warehouse')

    const name = form.querySelector<HTMLInputElement>('input')!
    name.value = 'Scanner 2'
    name.dispatchEvent(new Event('input'))
    await flushPromises()
    ;[...document.body.querySelectorAll('button')]
      .find((b) => b.textContent?.trim() === 'Save')!
      .click()
    await flushPromises()
    expect(create).toHaveBeenCalledWith({
      name: 'Scanner 2',
      notes: 'Ask the warehouse',
      tags: ['t1'],
      predecessor: 'p1',
    })
  })
})
