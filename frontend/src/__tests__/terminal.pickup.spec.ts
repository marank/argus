import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import TerminalListView from '@/views/terminal/TerminalListView.vue'
import TerminalPickupView from '@/views/terminal/TerminalPickupView.vue'

import { makeUser } from './helpers'
import { button, click, typeInto } from './dom'
import {
  bodyText,
  drawOn,
  field,
  mountPage,
  SIGNATURE,
  stubCanvas,
  unmountPages,
} from './portalHelpers'

const api = vi.hoisted(() => ({
  pickups: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  get: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  sign: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  people: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  staff: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
}))

vi.mock('@/api/requests', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/requests')>()),
  terminalApi: api,
}))

const TERMINAL = makeUser({ id: 'u-term', display_name: 'Terminal', is_terminal: true })
const SALES = { id: 'd1', name: 'Sales' }
const JANE = { id: 'u1', display_name: 'Jane Doe' }
const TOM = { id: 'u-it', display_name: 'Tom Tech' }

const model = (name: string) => ({
  id: `m-${name}`,
  name,
  full_name: name,
  designation: '',
  tracking: 'serialized' as const,
})

function allocation(
  overrides: Partial<Schemas['TerminalAllocationOut']> &
    Pick<Schemas['TerminalAllocationOut'], 'id'>,
): Schemas['TerminalAllocationOut'] {
  return {
    asset: null,
    consumable: null,
    license: null,
    quantity: 1,
    category_icon: 'laptop',
    handout_note: '',
    ...overrides,
  }
}

const LAPTOP = allocation({
  id: 'al-laptop',
  asset: {
    id: 'a1',
    inventory_number: 'NB-0001',
    serial_number: 'SN-111',
    status: 'reserved',
    model: model('ThinkPad T14'),
  },
  handout_note: 'Small scratch on the lid',
})
const MICE = allocation({
  id: 'al-mice',
  quantity: 2,
  consumable: {
    id: 's1',
    model: model('Logitech Mouse'),
    location: { id: 'l1', name: 'Store', full_name: 'HQ / Store' },
  },
})
// License seats are already assigned and not taken along.
const SEAT = allocation({
  id: 'al-seat',
  license: {
    id: 'seat1',
    model: model('Visio'),
    device: null,
  } as unknown as Schemas['LicenseSeatOut'],
})

function pickup(
  overrides: Partial<Schemas['TerminalPickupDetailOut']> = {},
): Schemas['TerminalPickupDetailOut'] {
  return {
    id: 'p1',
    number: 'R-2026-0042',
    title: 'Workshop in Munich',
    status: 'ready',
    requester: JANE,
    department: SALES,
    duration: 'temporary',
    start_date: '2026-10-20',
    end_date: '2026-10-24',
    pickup_at: '2026-10-20T09:00:00Z',
    pickup_location: null,
    prepared_by: TOM,
    handled_by: null,
    handover: null,
    skip_device_check: false,
    items: [
      { id: 'i1', label: 'ThinkPad T14', allocations: [LAPTOP] },
      { id: 'i2', label: 'Mouse', allocations: [MICE] },
      { id: 'i3', label: 'Visio', allocations: [SEAT] },
    ],
    ...overrides,
  }
}

describe('TerminalListView', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout', 'setInterval', 'clearInterval'] })
    Object.values(api).forEach((mock) => mock.mockReset())
  })
  afterEach(() => {
    unmountPages()
    vi.useRealTimers()
  })

  const listed: Schemas['TerminalPickupOut'][] = [
    {
      id: 'p1',
      number: 'R-2026-0042',
      title: 'Workshop in Munich',
      summary: '1× ThinkPad T14, 2× Logitech Mouse',
      requester: { id: 'u1', display_name: 'Jane Doe', employee_number: '4711', department: SALES },
      pickup_at: null,
      pickup_location: null,
      unit_count: 3,
    },
  ]

  it('lists the prepared pickups with who collects what', async () => {
    api.pickups.mockResolvedValue(listed)
    await mountPage(TerminalListView, { user: TERMINAL })
    const card = document.body.querySelector<HTMLAnchorElement>('a.card')!
    expect(card.textContent).toContain('Jane Doe')
    expect(card.textContent).toContain('Sales')
    expect(card.textContent).toContain('1× ThinkPad T14, 2× Logitech Mouse')
    expect(card.getAttribute('href')).toBe('/terminal/p1')
  })

  it('searches by name or number', async () => {
    api.pickups.mockResolvedValue(listed)
    await mountPage(TerminalListView, { user: TERMINAL })
    expect(api.pickups).toHaveBeenCalledWith(undefined)
    await typeInto(field('Search name or number…'), 'jane')
    await vi.advanceTimersByTimeAsync(300)
    expect(api.pickups).toHaveBeenLastCalledWith('jane')
  })

  it('shows pickups IT prepares meanwhile without touching the screen', async () => {
    api.pickups.mockResolvedValueOnce([])
    api.pickups.mockResolvedValue(listed)
    await mountPage(TerminalListView, { user: TERMINAL })
    expect(bodyText()).toContain('No pickups are prepared right now.')
    await vi.advanceTimersByTimeAsync(30_000)
    expect(bodyText()).toContain('Jane Doe')
  })
})

describe('TerminalPickupView', () => {
  beforeEach(() => {
    stubCanvas()
    Object.values(api).forEach((mock) => mock.mockReset())
    api.get.mockResolvedValue(pickup())
    api.sign.mockResolvedValue(pickup({ status: 'handed_out' }))
  })
  afterEach(() => {
    unmountPages()
    vi.restoreAllMocks()
    vi.useRealTimers()
  })

  async function open(detail = pickup()) {
    api.get.mockResolvedValue(detail)
    return mountPage(TerminalPickupView, {
      props: { id: detail.id },
      url: `/terminal/${detail.id}`,
      user: TERMINAL,
    })
  }

  const deviceRows = () => [...document.body.querySelectorAll('ul.devices > li')]
  const activeStep = () => document.body.querySelector('.steps li.active')?.textContent?.trim()

  async function sign() {
    await drawOn(document.body.querySelector('canvas')!)
  }

  it('lists the devices to check, without license seats', async () => {
    await open()
    expect(api.get).toHaveBeenCalledWith('p1')
    expect(activeStep()).toBe('1Check devices')
    expect(bodyText()).toContain('2 devices')
    expect(bodyText()).toContain('Return by')
    const rows = deviceRows().map((r) => r.textContent)
    expect(rows).toHaveLength(2)
    expect(rows[0]).toContain('ThinkPad T14')
    expect(rows[0]).toContain('NB-0001')
    expect(rows[0]).toContain('SN-111')
    expect(rows[0]).toContain('Noted by IT: Small scratch on the lid')
    expect(rows[1]).toContain('Logitech Mouse')
    expect(rows[1]).toContain('2×')
    expect(bodyText()).not.toContain('Visio')
  })

  it('says the devices may be kept when nothing has to come back', async () => {
    await open(pickup({ duration: 'permanent', end_date: null }))
    expect(bodyText()).toContain('Permanent')
    expect(bodyText()).not.toContain('Return by')
  })

  it('starts with who collects when IT skipped the device check', async () => {
    await open(pickup({ skip_device_check: true }))
    expect(activeStep()).toBe('1Who collects?')
    expect(bodyText()).toContain('Who is collecting the devices?')
    expect(bodyText()).not.toContain('Check devices')
  })

  it('goes back to the overview when the pickup cannot be loaded', async () => {
    api.get.mockRejectedValue(new ApiError(404, 'Not found.'))
    const { router } = await mountPage(TerminalPickupView, {
      props: { id: 'gone' },
      url: '/terminal/gone',
      user: TERMINAL,
    })
    expect(router.currentRoute.value.name).toBe('terminal')
  })

  it('hands the devices to the requester after signing', async () => {
    await open()
    await click(button('Everything checked'))
    expect(activeStep()).toBe('2Who collects?')
    // The requester is preselected.
    expect(document.body.querySelector('.choice.active')!.textContent).toContain('I am Jane Doe')
    await click(button('Continue'))
    expect(activeStep()).toBe('3Sign')
    const receipt = document.body.querySelector('.receipt')!.textContent
    expect(receipt).toContain('Jane Doe')
    expect(receipt).toContain('Tom Tech')
    expect(receipt).toContain('NB-0001')

    expect(button('Sign and finish').disabled).toBe(true)
    await sign()
    expect(button('Sign and finish').disabled).toBe(false)
    await click(button('Sign and finish'))

    expect(api.sign).toHaveBeenCalledWith('p1', {
      handed_out_by: 'u-it',
      received_by: 'u1',
      received_by_name: 'Jane Doe',
      signature: SIGNATURE,
      notes: '',
      allocation_notes: [],
    } satisfies Schemas['TerminalSignIn'])
    expect(bodyText()).toContain('Thank you!')
    expect(bodyText()).toContain('The handover to Jane Doe has been recorded.')
  })

  it('records notes on damaged devices and general remarks', async () => {
    await open()
    const laptop = deviceRows()[0]!
    await click(laptop.querySelector('button')!)
    await typeInto(laptop.querySelector('textarea')!, 'Dent on the corner')
    // Closing the note keeps it and marks the device.
    await click(laptop.querySelector('button')!)
    expect(laptop.querySelector('.own-note')?.textContent).toContain('Dent on the corner')
    expect(laptop.querySelector('button')!.textContent).toContain('Note added')
    // A note left blank is not sent.
    const mice = deviceRows()[1]!
    await click(mice.querySelector('button')!)
    await typeInto(mice.querySelector('textarea')!, '   ')
    await typeInto(field('Further remarks (optional)'), 'Bag missing')

    await click(button('Everything checked'))
    await click(button('Continue'))
    const receipt = document.body.querySelector('.receipt')!.textContent
    expect(receipt).toContain('Dent on the corner')
    expect(receipt).toContain('Bag missing')
    await sign()
    await click(button('Sign and finish'))

    expect(api.sign).toHaveBeenCalledWith(
      'p1',
      expect.objectContaining({
        notes: 'Bag missing',
        allocation_notes: [{ allocation: 'al-laptop', note: 'Dent on the corner' }],
      }),
    )
  })

  describe('someone else collects', () => {
    beforeEach(() => {
      vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    })

    async function chooseSomeoneElse() {
      await click(button('Everything checked'))
      await click(document.body.querySelectorAll('.choice')[1]!)
    }

    it('needs a name before continuing', async () => {
      await open()
      await chooseSomeoneElse()
      expect(button('Continue').disabled).toBe(true)
      await typeInto(field('Name or employee number'), '  ')
      expect(button('Continue').disabled).toBe(true)
    })

    it('picks a colleague from the search', async () => {
      api.people.mockResolvedValue([
        { id: 'u-max', display_name: 'Max Muster', employee_number: '0815', department: SALES },
      ] satisfies Schemas['TerminalPersonOut'][])
      await open()
      await chooseSomeoneElse()
      await typeInto(field('Name or employee number'), 'ma')
      await vi.advanceTimersByTimeAsync(250)
      expect(api.people).toHaveBeenCalledWith('ma')
      const option = document.body.querySelector('[role="option"]')!
      expect(option.textContent).toContain('Max Muster')
      expect(option.textContent).toContain('0815')
      await click(option)
      expect(field('Name or employee number').value).toBe('Max Muster')

      await click(button('Continue'))
      expect(document.body.querySelector('.receipt')!.textContent).toContain(
        'Collecting on behalf of Jane Doe',
      )
      await sign()
      await click(button('Sign and finish'))
      expect(api.sign).toHaveBeenCalledWith(
        'p1',
        expect.objectContaining({ received_by: 'u-max', received_by_name: 'Max Muster' }),
      )
    })

    it('does not search for a single letter', async () => {
      await open()
      await chooseSomeoneElse()
      await typeInto(field('Name or employee number'), 'm')
      await vi.advanceTimersByTimeAsync(250)
      expect(api.people).not.toHaveBeenCalled()
    })

    it('records the typed name of someone not found', async () => {
      api.people.mockResolvedValue([])
      await open()
      await chooseSomeoneElse()
      await typeInto(field('Name or employee number'), 'Courier Smith')
      await vi.advanceTimersByTimeAsync(250)
      await click(button('Continue'))
      await sign()
      await click(button('Sign and finish'))
      expect(api.sign).toHaveBeenCalledWith(
        'p1',
        expect.objectContaining({ received_by: null, received_by_name: 'Courier Smith' }),
      )
    })

    it('forgets the picked colleague when the name is changed afterwards', async () => {
      api.people.mockResolvedValue([
        { id: 'u-max', display_name: 'Max Muster', employee_number: '', department: null },
      ])
      await open()
      await chooseSomeoneElse()
      await typeInto(field('Name or employee number'), 'max')
      await vi.advanceTimersByTimeAsync(250)
      await click(document.body.querySelector('[role="option"]')!)
      await typeInto(field('Name or employee number'), 'Max Mustermann jr.')
      await click(button('Continue'))
      await sign()
      await click(button('Sign and finish'))
      expect(api.sign).toHaveBeenCalledWith(
        'p1',
        expect.objectContaining({ received_by: null, received_by_name: 'Max Mustermann jr.' }),
      )
    })
  })

  it('cannot be finished once the signature is cleared', async () => {
    await open(pickup({ skip_device_check: true }))
    await click(button('Continue'))
    await sign()
    await click(button('Clear'))
    expect(button('Sign and finish').disabled).toBe(true)
  })

  it('shows the error and stays on the signature when recording fails', async () => {
    api.sign.mockRejectedValue(new ApiError(409, 'The pickup was taken back by IT.'))
    await open(pickup({ skip_device_check: true }))
    await click(button('Continue'))
    await sign()
    await click(button('Sign and finish'))
    expect(bodyText()).toContain('The pickup was taken back by IT.')
    expect(bodyText()).not.toContain('Thank you!')
    expect(button('Sign and finish').disabled).toBe(false)
  })

  it('returns to the overview a while after finishing', async () => {
    vi.useFakeTimers({ toFake: ['setTimeout', 'clearTimeout'] })
    const { router } = await open(pickup({ skip_device_check: true }))
    await click(button('Continue'))
    await sign()
    await click(button('Sign and finish'))
    expect(router.currentRoute.value.name).toBe('terminal-pickup')
    await vi.advanceTimersByTimeAsync(8000)
    expect(router.currentRoute.value.name).toBe('terminal')
  })

  it('asks before cancelling and stays when the pickup is continued', async () => {
    const { router } = await open()
    await click(button('Cancel'))
    expect(bodyText()).toContain('Cancel the pickup? Your entries will be lost.')
    await click(button('Continue pickup'))
    expect(router.currentRoute.value.name).toBe('terminal-pickup')

    await click(button('Cancel'))
    await click(button('Yes, cancel'))
    expect(router.currentRoute.value.name).toBe('terminal')
    expect(api.sign).not.toHaveBeenCalled()
  })

  it('names who prepared the pickup, or who handled the request without one', async () => {
    await open(
      pickup({
        skip_device_check: true,
        prepared_by: null,
        handled_by: { id: 'u-h', display_name: 'Hanna Help' },
      }),
    )
    await click(button('Continue'))
    expect(document.body.querySelector('.handed-out-by')!.textContent).toContain('Hanna Help')
    await sign()
    await click(button('Sign and finish'))
    expect(api.sign).toHaveBeenCalledWith('p1', expect.objectContaining({ handed_out_by: 'u-h' }))
  })

  it('loads the IT staff to change who handed out', async () => {
    api.staff.mockResolvedValue([TOM, { id: 'u-h', display_name: 'Hanna Help' }])
    await open(pickup({ skip_device_check: true }))
    await click(button('Continue'))
    await click(button('Change'))
    expect(api.staff).toHaveBeenCalledOnce()
    expect(document.body.querySelector('.handed-out-by .n-select')).not.toBeNull()
  })
})
