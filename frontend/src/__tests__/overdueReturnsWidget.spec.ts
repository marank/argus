import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createI18n } from 'vue-i18n'

import OverdueReturnsWidget from '@/components/dashboard/widgets/OverdueReturnsWidget.vue'
import type { ITOverview, OverdueReturn } from '@/types/dashboard'

const confirm = vi.fn<(content: string) => Promise<boolean>>()
const remind = vi.fn<(id: string) => Promise<unknown>>()

vi.mock('@/composables/useConfirm', () => ({ useConfirm: () => confirm }))
vi.mock('@/api/reservations', () => ({ reservationsApi: { remind: (id: string) => remind(id) } }))
vi.mock('@/api/dashboard', () => ({
  dashboardApi: { overdueReturns: () => Promise.resolve([row]) },
}))
vi.mock('naive-ui', async (importOriginal) => ({
  ...(await importOriginal<typeof import('naive-ui')>()),
  useMessage: () => ({ success: vi.fn<() => void>(), error: vi.fn<() => void>() }),
}))

const row: OverdueReturn = {
  id: 'r1',
  number: 'RES-2026-00011',
  title: 'Inventory scanners',
  end_date: '2026-10-16',
  requester: { id: 'u1', username: 'pwolf', display_name: 'Paul Wolf' },
  can_remind: true,
  reminded_at: null,
  reminded_by: null,
}

async function mountWidget() {
  const i18n = createI18n({ legacy: false, locale: 'en', missingWarn: false, fallbackWarn: false })
  const wrapper = mount(OverdueReturnsWidget, {
    props: { data: {} as ITOverview, options: {} },
    global: { plugins: [i18n], stubs: { RouterLink: { template: '<a><slot /></a>' } } },
  })
  await flushPromises()
  return wrapper
}

const remindButton = (wrapper: Awaited<ReturnType<typeof mountWidget>>) =>
  wrapper.findAll('button').find((b) => b.text().includes('remind'))!

describe('overdue returns widget', () => {
  beforeEach(() => {
    confirm.mockReset()
    remind.mockReset()
  })

  it('asks before sending and sends nothing when cancelled', async () => {
    confirm.mockResolvedValue(false)
    const wrapper = await mountWidget()
    await remindButton(wrapper).trigger('click')
    await flushPromises()
    expect(confirm).toHaveBeenCalledOnce()
    expect(remind).not.toHaveBeenCalled()
  })

  it('sends the reminder once confirmed', async () => {
    confirm.mockResolvedValue(true)
    remind.mockResolvedValue({})
    const wrapper = await mountWidget()
    await remindButton(wrapper).trigger('click')
    await flushPromises()
    expect(remind).toHaveBeenCalledWith('r1')
  })
})
