import { flushPromises, mount } from '@vue/test-utils'
import { NDialogProvider, NMessageProvider } from 'naive-ui'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h } from 'vue'

import { ApiError } from '@/api/client'
import ErrorPopover from '@/components/common/ErrorPopover.vue'
import CrudPage from '@/components/crud/CrudPage.vue'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

import { errorPopoverText, fieldErrors } from './dom'
import { makeUser } from './helpers'

interface Maker {
  id: string
  name: string
  notes: string
  is_active: boolean
}

const ACME: Maker = { id: 'm1', name: 'Acme', notes: '', is_active: true }

function makeResource() {
  const api = {
    list: vi.fn<(params: object) => Promise<{ items: Maker[]; count: number }>>(async () => ({
      items: [ACME],
      count: 1,
    })),
    create: vi.fn<(data: Omit<Maker, 'id'>) => Promise<Maker>>(async (data) => ({
      id: 'm2',
      ...data,
    })),
    update: vi.fn<(id: string, data: Omit<Maker, 'id'>) => Promise<Maker>>(async (id, data) => ({
      id,
      ...data,
    })),
    remove: vi.fn<(id: string) => Promise<true>>(async () => true as const),
  }
  const resource = defineResource<Maker>({
    key: 'manufacturers',
    permission: 'manufacturers',
    api,
    ordering: 'name',
    title: (m) => m.name,
    columns: [{ key: 'name', label: 'common.name', sorter: 'name' }],
    sections: [
      {
        fields: [
          { key: 'name', label: 'common.name', type: 'text', required: true },
          { key: 'is_active', label: 'common.active', type: 'switch' },
        ],
      },
      { fields: [{ key: 'notes', label: 'common.notes', type: 'textarea' }] },
    ],
    defaults: () => ({ name: '', notes: '', is_active: true }),
    toForm: ({ id: _id, ...rest }) => rest,
  })
  return { api, resource }
}

async function mountPage(permission: 'read' | 'write' = 'write') {
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().user = makeUser({ is_it_staff: true, permissions: { manufacturers: permission } })
  const { api, resource } = makeResource()
  const wrapper = mount(
    defineComponent({
      render: () =>
        h(NMessageProvider, null, {
          default: () => [
            h(ErrorPopover),
            h(NDialogProvider, null, { default: () => h(CrudPage, { resource }) }),
          ],
        }),
    }),
    { attachTo: document.body, global: { plugins: [i18n, pinia] } },
  )
  await flushPromises()
  return { api, wrapper }
}

const buttons = (text: string) =>
  [...document.body.querySelectorAll('button')].filter((b) => b.textContent?.trim() === text)
const button = (text: string) => {
  const found = buttons(text)
  if (!found.length) throw new Error(`no button "${text}"`)
  return found.at(-1)!
}
const drawerInput = () => document.body.querySelector<HTMLInputElement>('.ar-form input')!

function typeInto(input: HTMLInputElement, value: string) {
  input.value = value
  input.dispatchEvent(new Event('input'))
}

describe('CrudPage', () => {
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

  async function page(permission: 'read' | 'write' = 'write') {
    const result = await mountPage(permission)
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('loads and lists the records', async () => {
    const { api, wrapper } = await page()
    expect(api.list).toHaveBeenCalledWith(expect.objectContaining({ page: 1, ordering: 'name' }))
    expect(wrapper.text()).toContain('Acme')
  })

  it('creates a record once the required fields are filled', async () => {
    const { api } = await page()
    button('Manufacturer').click()
    await flushPromises()
    expect(document.body.textContent).toContain('Manufacturer · Create')
    expect(button('Save').disabled).toBe(true)

    typeInto(drawerInput(), 'Globex')
    await flushPromises()
    expect(button('Save').disabled).toBe(false)
    button('Save').click()
    await flushPromises()

    expect(api.create).toHaveBeenCalledWith({ name: 'Globex', notes: '', is_active: true })
    // Saved: the list is fetched again.
    expect(api.list).toHaveBeenCalledTimes(2)
  })

  it('edits a record from its row', async () => {
    const { api, wrapper } = await page()
    await wrapper.find('tbody tr').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('Manufacturer · Acme')
    expect(drawerInput().value).toBe('Acme')
    typeInto(drawerInput(), 'Acme Corp')
    await flushPromises()
    button('Save').click()
    await flushPromises()
    expect(api.update).toHaveBeenCalledWith('m1', { name: 'Acme Corp', notes: '', is_active: true })
  })

  it('shows validation errors at the field', async () => {
    const { api } = await page()
    api.create.mockRejectedValueOnce(new ApiError(400, 'Check the form.', { name: ['Taken.'] }))
    button('Manufacturer').click()
    await flushPromises()
    typeInto(drawerInput(), 'Acme')
    await flushPromises()
    button('Save').click()
    await flushPromises()
    expect(fieldErrors()).toEqual(['Taken.'])
    // The popover points at the first refused field.
    expect(errorPopoverText()).toBe('Taken.')
    expect(api.list).toHaveBeenCalledOnce()
  })

  it('deletes a record after confirming', async () => {
    const { api, wrapper } = await page()
    await wrapper.find('button[title="Delete"]').trigger('click')
    await flushPromises()
    expect(document.body.textContent).toContain('Acme: Delete this record permanently?')
    button('Confirm').click()
    await flushPromises()
    expect(api.remove).toHaveBeenCalledWith('m1')
    expect(api.list).toHaveBeenCalledTimes(2)
  })

  it('keeps the record when deleting is cancelled', async () => {
    const { api, wrapper } = await page()
    await wrapper.find('button[title="Delete"]').trigger('click')
    await flushPromises()
    button('Cancel').click()
    await flushPromises()
    expect(api.remove).not.toHaveBeenCalled()
  })

  it('opens records read-only without the right to change them', async () => {
    const { wrapper } = await page('read')
    expect(buttons('Manufacturer')).toEqual([])
    expect(wrapper.find('button[title="Delete"]').exists()).toBe(false)
    await wrapper.find('tbody tr').trigger('click')
    await flushPromises()
    expect(buttons('Save')).toEqual([])
    expect(buttons('Close').length).toBeGreaterThan(0)
  })

  it('searches the list', async () => {
    vi.useFakeTimers()
    try {
      const { api, wrapper } = await page()
      await wrapper.find('.toolbar input').setValue('acm')
      await vi.advanceTimersByTimeAsync(300)
      expect(api.list).toHaveBeenLastCalledWith(expect.objectContaining({ q: 'acm' }))
    } finally {
      vi.useRealTimers()
    }
  })
})
