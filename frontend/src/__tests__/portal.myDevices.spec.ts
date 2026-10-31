import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import MyDeviceDetailView from '@/views/portal/MyDeviceDetailView.vue'
import MyDevicesView from '@/views/portal/MyDevicesView.vue'
import MyIssuesView from '@/views/portal/MyIssuesView.vue'
import MyLicensesView from '@/views/portal/MyLicensesView.vue'

import { button, click, fakeMatchMedia, hasButton, typeInto } from './dom'
import { bodyText, field, mountPage, unmountPages } from './portalHelpers'

const api = vi.hoisted(() => ({
  myAssets: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  myAsset: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  myIssues: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  myLicenses: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  reportIssue: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
}))

vi.mock('@/api/requests', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/api/requests')>()
  return { ...original, portalApi: { ...original.portalApi, ...api } }
})

const modelRef = (name: string) => ({
  id: `m-${name}`,
  name,
  full_name: name,
  designation: '',
  tracking: 'serialized' as const,
})

function issue(overrides: Partial<Schemas['OwnIssueOut']> = {}): Schemas['OwnIssueOut'] {
  return {
    id: 'is1',
    kind: 'defect',
    status: 'open',
    description: 'Fan is loud',
    last_message: 'Fan is loud',
    created_at: '2026-10-05T08:00:00Z',
    unseen_update: false,
    ...overrides,
  }
}

function myAsset(overrides: Partial<Schemas['MyAssetOut']> = {}): Schemas['MyAssetOut'] {
  return {
    id: 'a1',
    inventory_number: 'NB-0001',
    serial_number: 'SN-111',
    model: modelRef('ThinkPad T14'),
    category: 'Laptops',
    category_icon: 'laptop',
    assigned_since: '2026-09-01',
    return_due: null,
    asset_request_number: null,
    issues: [],
    ...overrides,
  }
}

const PLACEHOLDER = 'What does not work, since when, what have you tried?'

describe('MyDevicesView', () => {
  beforeEach(() => Object.values(api).forEach((mock) => mock.mockReset()))
  afterEach(unmountPages)

  const rowOf = (number: string) =>
    [...document.body.querySelectorAll('tbody tr')].find((r) => r.textContent?.includes(number))!

  it('lists the devices with when they are due back', async () => {
    api.myAssets.mockResolvedValue([
      myAsset(),
      myAsset({
        id: 'a2',
        inventory_number: 'BM-0003',
        model: modelRef('Epson beamer'),
        return_due: '2026-10-24',
        asset_request_number: 'R-9',
      }),
    ])
    await mountPage(MyDevicesView)
    expect(rowOf('NB-0001').textContent).toContain('permanent')
    expect(rowOf('BM-0003').textContent).toContain('10/24/2026')
  })

  it('marks returns that are overdue', async () => {
    api.myAssets.mockResolvedValue([
      myAsset({ return_due: '2020-01-31', asset_request_number: 'R-1' }),
      myAsset({ id: 'a2', inventory_number: 'NB-0002', return_due: '2099-01-31' }),
    ])
    await mountPage(MyDevicesView)
    expect(rowOf('NB-0001').querySelector('.overdue')).not.toBeNull()
    expect(rowOf('NB-0002').querySelector('.overdue')).toBeNull()
  })

  describe('on a phone', () => {
    let restore: () => void
    beforeEach(() => {
      restore = fakeMatchMedia(375)
    })
    afterEach(() => {
      restore()
    })

    it('shows one card per device with return date and report button', async () => {
      api.myAssets.mockResolvedValue([
        myAsset({ return_due: '2020-01-31', asset_request_number: 'R-1', issues: [issue()] }),
      ])
      const { router } = await mountPage(MyDevicesView)
      expect(document.body.querySelector('table')).toBeNull()
      const card = document.body.querySelector<HTMLElement>('.card')!
      expect(card.textContent).toContain('NB-0001')
      expect(card.textContent).toContain('Return overdue since')
      expect(card.querySelector('.report-badge')?.textContent).toBe('Report open')

      await click(button('Report a problem'))
      expect(router.currentRoute.value.name).not.toBe('portal-device')
      expect(document.body.querySelector('.n-modal')?.textContent).toContain('ThinkPad T14')
    })
  })

  it('marks devices with an open or running problem report', async () => {
    api.myAssets.mockResolvedValue([
      myAsset({ issues: [issue({ status: 'resolved' })] }),
      myAsset({ id: 'a2', inventory_number: 'NB-0002', issues: [issue()] }),
      myAsset({
        id: 'a3',
        inventory_number: 'NB-0003',
        issues: [issue({ status: 'in_progress' })],
      }),
    ])
    await mountPage(MyDevicesView)
    expect(rowOf('NB-0001').querySelector('.report-badge')).toBeNull()
    expect(rowOf('NB-0002').querySelector('.report-badge')?.textContent).toBe('Report open')
    expect(rowOf('NB-0003').querySelector('.report-badge')?.textContent).toBe('Report in progress')
  })

  it('opens a device from its row', async () => {
    api.myAssets.mockResolvedValue([myAsset()])
    const { router } = await mountPage(MyDevicesView)
    await click(rowOf('NB-0001'))
    expect(router.currentRoute.value.name).toBe('portal-device')
    expect(router.currentRoute.value.params.id).toBe('a1')
  })

  it('reports a problem with a device and reloads the list', async () => {
    api.myAssets.mockResolvedValue([myAsset()])
    api.reportIssue.mockResolvedValue(issue())
    const { router } = await mountPage(MyDevicesView)
    await click(button('Report a problem'))
    // The button sits in the row but does not open the device.
    expect(router.currentRoute.value.name).not.toBe('portal-device')
    const modal = document.body.querySelector('.n-modal')!
    expect(modal.textContent).toContain('ThinkPad T14')
    expect(modal.textContent).toMatch(/NB-0001\s+· SN-111/)

    expect(button('Send to IT').disabled).toBe(true)
    await click(modal.querySelector<HTMLInputElement>('input[value="damage"]')!)
    await typeInto(field(PLACEHOLDER), 'Display cracked')
    await click(button('Send to IT'))

    expect(api.reportIssue).toHaveBeenCalledWith('a1', {
      kind: 'damage',
      description: 'Display cracked',
    })
    expect(bodyText()).toContain('Report sent to IT')
    expect(api.myAssets).toHaveBeenCalledTimes(2)
  })

  it('keeps the report open with its text when sending fails', async () => {
    api.myAssets.mockResolvedValue([myAsset()])
    api.reportIssue.mockRejectedValue(new ApiError(400, 'The device is no longer yours.'))
    await mountPage(MyDevicesView)
    await click(button('Report a problem'))
    await typeInto(field(PLACEHOLDER), 'Display cracked')
    await click(button('Send to IT'))
    expect(bodyText()).toContain('The device is no longer yours.')
    expect(field(PLACEHOLDER).value).toBe('Display cracked')
  })

  it('starts the next report empty', async () => {
    api.myAssets.mockResolvedValue([myAsset()])
    await mountPage(MyDevicesView)
    await click(button('Report a problem'))
    await typeInto(field(PLACEHOLDER), 'Draft')
    await click(button('Cancel'))
    await click(button('Report a problem'))
    expect(field(PLACEHOLDER).value).toBe('')
  })

  it('offers no reports when they are switched off', async () => {
    api.myAssets.mockResolvedValue([myAsset()])
    await mountPage(MyDevicesView, { flags: { issues: false } })
    expect(hasButton('Report a problem')).toBe(false)
  })

  it('says when no device is assigned', async () => {
    api.myAssets.mockResolvedValue([])
    await mountPage(MyDevicesView)
    expect(bodyText()).toContain('No devices are assigned to you.')
  })
})

describe('MyDeviceDetailView', () => {
  beforeEach(() => Object.values(api).forEach((mock) => mock.mockReset()))
  afterEach(unmountPages)

  it('shows the loan’s due date with the request it came from', async () => {
    api.myAsset.mockResolvedValue(
      myAsset({ return_due: '2026-10-24', asset_request_number: 'R-9' }),
    )
    await mountPage(MyDeviceDetailView, { props: { id: 'a1' } })
    expect(api.myAsset).toHaveBeenCalledWith('a1')
    expect(bodyText()).toContain('10/24/2026 · R-9')
  })

  it('marks an overdue return', async () => {
    api.myAsset.mockResolvedValue(
      myAsset({ return_due: '2020-01-31', asset_request_number: 'R-9' }),
    )
    await mountPage(MyDeviceDetailView, { props: { id: 'a1' } })
    expect(document.body.querySelector('dd.warning')?.textContent).toContain('R-9 · overdue')
  })

  it('lists the reports with IT’s latest answer, linking to the conversation', async () => {
    api.myAsset.mockResolvedValue(
      myAsset({
        issues: [
          issue({ id: 'is1', last_message: 'We ordered a new fan.', status: 'in_progress' }),
          // Without an answer the description is not repeated.
          issue({
            id: 'is2',
            kind: 'lost',
            description: 'Charger lost',
            last_message: 'Charger lost',
          }),
        ],
      }),
    )
    await mountPage(MyDeviceDetailView, { props: { id: 'a1' } })
    const [first, second] = [...document.body.querySelectorAll('.issues a')]
    expect(first!.getAttribute('href')).toBe('/portal/issues/is1')
    expect(first!.textContent).toContain('Not working')
    expect(first!.textContent).toContain('We ordered a new fan.')
    expect(second!.textContent).toContain('Lost or stolen')
    expect(second!.querySelector('.answer')).toBeNull()
  })

  it('says when there are no reports', async () => {
    api.myAsset.mockResolvedValue(myAsset())
    await mountPage(MyDeviceDetailView, { props: { id: 'a1' } })
    expect(bodyText()).toContain('There are no reports for this device.')
  })

  it('reports a problem and shows it after reloading', async () => {
    api.myAsset.mockResolvedValueOnce(myAsset())
    api.myAsset.mockResolvedValueOnce(myAsset({ issues: [issue({ description: 'No sound' })] }))
    api.reportIssue.mockResolvedValue(issue())
    await mountPage(MyDeviceDetailView, { props: { id: 'a1' } })
    await click(button('Report a problem'))
    await typeInto(field(PLACEHOLDER), 'No sound')
    await click(button('Send to IT'))
    expect(api.reportIssue).toHaveBeenCalledWith('a1', { kind: 'defect', description: 'No sound' })
    expect(document.body.querySelector('.issues')?.textContent).toContain('No sound')
  })
})

describe('MyIssuesView', () => {
  beforeEach(() => Object.values(api).forEach((mock) => mock.mockReset()))
  afterEach(unmountPages)

  function ownIssue(
    overrides: Partial<Schemas['OwnIssueWithDeviceOut']> = {},
  ): Schemas['OwnIssueWithDeviceOut'] {
    return {
      ...issue(),
      asset: {
        id: 'a1',
        inventory_number: 'NB-0001',
        model: modelRef('ThinkPad T14'),
        category_icon: 'laptop',
      },
      still_assigned: true,
      ...overrides,
    }
  }

  it('shows open reports before resolved ones, in sections', async () => {
    api.myIssues.mockResolvedValue([
      ownIssue({ id: 'old', status: 'resolved', description: 'Old problem' }),
      ownIssue({ id: 'new', status: 'in_progress', description: 'Current problem' }),
    ])
    await mountPage(MyIssuesView)
    const rows = [...document.body.querySelectorAll('tbody tr')].map((r) => r.textContent)
    expect(rows[0]).toContain('Open')
    expect(rows[1]).toContain('Current problem')
    expect(rows[2]).toContain('Resolved')
    expect(rows[3]).toContain('Old problem')
  })

  it('notes when the device has been returned since', async () => {
    api.myIssues.mockResolvedValue([ownIssue({ still_assigned: false })])
    await mountPage(MyIssuesView)
    expect(document.body.querySelector('tbody')!.textContent).toContain('NB-0001 · returned')
  })

  it('opens the conversation of a report', async () => {
    api.myIssues.mockResolvedValue([ownIssue({ id: 'is9' })])
    const { router } = await mountPage(MyIssuesView)
    const row = [...document.body.querySelectorAll('tbody tr')].find((r) =>
      r.textContent?.includes('Fan is loud'),
    )!
    await click(row)
    expect(router.currentRoute.value.name).toBe('portal-issue')
    expect(router.currentRoute.value.params.id).toBe('is9')
  })

  it('says when nothing was reported', async () => {
    api.myIssues.mockResolvedValue([])
    await mountPage(MyIssuesView)
    expect(bodyText()).toContain('No reports yet.')
  })
})

describe('MyLicensesView', () => {
  beforeEach(() => {
    vi.useFakeTimers({ toFake: ['Date'] })
    vi.setSystemTime(new Date(2026, 9, 12, 10, 0))
    Object.values(api).forEach((mock) => mock.mockReset())
  })
  afterEach(() => {
    unmountPages()
    vi.useRealTimers()
  })

  function license(overrides: Partial<Schemas['OwnLicenseOut']> = {}): Schemas['OwnLicenseOut'] {
    return {
      id: 'l1',
      model: modelRef('Visio'),
      category_icon: 'app-window',
      device: null,
      valid_until: null,
      is_expired: false,
      assigned_at: '2026-01-10',
      ...overrides,
    }
  }

  const rowOf = (name: string) =>
    [...document.body.querySelectorAll('tbody tr')].find((r) => r.textContent?.includes(name))!
      .textContent

  it('says whether a seat is personal or on one of the employee’s devices', async () => {
    api.myLicenses.mockResolvedValue([
      license(),
      license({
        id: 'l2',
        model: modelRef('Office'),
        device: { id: 'a1', inventory_number: 'NB-0001', model: modelRef('ThinkPad T14') },
      }),
    ])
    await mountPage(MyLicensesView)
    expect(rowOf('Visio')).toContain('You personally')
    expect(rowOf('Office')).toContain('NB-0001 · ThinkPad T14')
  })

  it('warns about licenses that expired or expire within the warning period', async () => {
    api.myLicenses.mockResolvedValue([
      license({ model: modelRef('Perpetual'), valid_until: null }),
      license({ id: 'l2', model: modelRef('Gone'), valid_until: '2026-10-01', is_expired: true }),
      // The default warning period is 60 days.
      license({ id: 'l3', model: modelRef('Soon'), valid_until: '2026-11-30' }),
      license({ id: 'l4', model: modelRef('Later'), valid_until: '2027-06-30' }),
    ])
    await mountPage(MyLicensesView)
    expect(rowOf('Perpetual')).toContain('perpetual')
    expect(rowOf('Gone')).toContain('expired')
    expect(rowOf('Soon')).toContain('expires soon')
    expect(rowOf('Later')).not.toMatch(/expire/)
  })
})
