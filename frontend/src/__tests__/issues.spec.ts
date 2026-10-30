import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { reactive } from 'vue'

import { ApiError } from '@/api/client'
import { issuesApi } from '@/api/inventory'
import { portalApi } from '@/api/requests'
import type { Schemas } from '@/api/types'
import IssueConversation from '@/components/issues/IssueConversation.vue'
import IssueDetailView from '@/views/issues/IssueDetailView.vue'
import IssueListView from '@/views/inventory/IssueListView.vue'

import { button, click, hasButton } from './dom'
import {
  bodyText,
  check,
  locationRef,
  modelRef,
  mountPage,
  page,
  stubPickers,
  type,
  userRef,
} from './inventoryHelpers'

const REPORTER = userRef('Rita Reporter', 'u1')
const TECH = userRef('Ian Tech', 'u9')

const message = (
  id: string,
  side: 'reporter' | 'it',
  text: string,
  author: Schemas['UserRefOut'] | null = side === 'it' ? TECH : REPORTER,
): Schemas['IssueEntryOut'] => ({
  id,
  kind: 'message',
  side,
  text,
  author,
  created_at: '2026-10-02T09:00:00Z',
})

const statusChange = (
  id: string,
  status: Schemas['AssetIssueStatus'],
  author: Schemas['UserRefOut'] | null = TECH,
): Schemas['IssueEntryOut'] => ({
  id,
  kind: 'status',
  side: 'it',
  status,
  text: '',
  author,
  created_at: '2026-10-02T10:00:00Z',
})

function makeIssue(
  overrides: Partial<Schemas['AssetIssueDetailOut']> = {},
): Schemas['AssetIssueDetailOut'] {
  return {
    id: 'i1',
    kind: 'defect',
    status: 'open',
    description: 'The fan is very loud.',
    created_at: '2026-10-01T08:00:00Z',
    reported_by: {
      id: 'u1',
      display_name: 'Rita Reporter',
      email: 'rita@example.com',
      phone: '',
      job_title: 'Accountant',
      department: 'Finance',
    },
    handled_by: null,
    resolved_at: null,
    assigned_team: null,
    assignee: null,
    entries: [],
    other_issues: [],
    still_assigned: true,
    unseen_update: false,
    asset: {
      id: 'a1',
      inventory_number: 'NB-0042',
      serial_number: 'SN-1',
      hostname: 'nb-0042',
      model: modelRef(),
      category: 'Laptops',
      category_icon: 'laptop',
      status: 'in_use',
      location: locationRef(),
      assigned_to: REPORTER,
      assigned_since: '2026-01-10T09:00:00Z',
      purchase_date: '2025-03-01',
      warranty_until: '2028-03-01',
    },
    ...overrides,
  }
}

let unmount: (() => void) | null = null
afterEach(() => {
  unmount?.()
  unmount = null
  document.body.innerHTML = ''
  localStorage.clear()
  vi.restoreAllMocks()
})

describe('IssueConversation', () => {
  async function conversation(
    issue: Schemas['AssetIssueDetailOut'],
    viewer: 'reporter' | 'it',
    canWrite = true,
  ) {
    const props = reactive({
      issue,
      viewer,
      canWrite,
      busy: false,
      onSend: vi.fn<(text: string) => void>(),
      onStatus: vi.fn<(status: string, text: string) => void>(),
    })
    const { wrapper } = await mountPage(IssueConversation, props)
    unmount = () => wrapper.unmount()
    return props
  }

  const items = () =>
    [...document.body.querySelectorAll('.conversation > li')].map((li) => li.textContent ?? '')
  const mine = () =>
    [...document.body.querySelectorAll('.message.mine .text')].map((el) => el.textContent)
  const theirs = () =>
    [...document.body.querySelectorAll('.message:not(.mine) .text')].map((el) => el.textContent)

  const ISSUE = makeIssue({
    entries: [
      message('m1', 'it', 'Can you bring it by?'),
      statusChange('s1', 'in_progress'),
      message('m2', 'reporter', 'Will do on Monday.'),
      statusChange('s2', 'resolved', null),
    ],
  })

  it('opens with the report, then messages and status changes in order', async () => {
    await conversation(ISSUE, 'it')
    const shown = items()
    expect(shown).toHaveLength(5)
    expect(shown[0]).toContain('Report · Not working')
    expect(shown[0]).toContain('The fan is very loud.')
    expect(shown[1]).toContain('Can you bring it by?')
    expect(shown[2]).toContain('Ian Tech started working on the report')
    expect(shown[3]).toContain('Will do on Monday.')
    expect(shown[4]).toContain('Someone marked the report as resolved')
  })

  it("puts IT's messages on IT's own side", async () => {
    await conversation(ISSUE, 'it')
    expect(mine()).toEqual(['Can you bring it by?'])
    expect(theirs()).toEqual(['The fan is very loud.', 'Will do on Monday.'])
  })

  it("puts the reporter's messages on the reporter's own side", async () => {
    await conversation(ISSUE, 'reporter')
    expect(mine()).toEqual(['The fan is very loud.', 'Will do on Monday.'])
    expect(theirs()).toEqual(['Can you bring it by?'])
  })

  it('names the side of each message', async () => {
    await conversation(ISSUE, 'reporter')
    const sides = [...document.body.querySelectorAll('.message .side')].map((el) => el.textContent)
    expect(sides).toEqual(['Reporter', 'IT', 'Reporter'])
  })

  it('sends a typed message, trimmed, and nothing while the field is blank', async () => {
    const props = await conversation(makeIssue(), 'it')
    expect(button('Send').disabled).toBe(true)
    await type(document.body.querySelector<HTMLInputElement>('textarea')!, '   ')
    expect(button('Send').disabled).toBe(true)
    await type(document.body.querySelector<HTMLInputElement>('textarea')!, '  On my way.  ')
    await click('Send')
    expect(props.onSend).toHaveBeenCalledWith('On my way.')
  })

  it('sends with Ctrl+Enter', async () => {
    const props = await conversation(makeIssue(), 'reporter')
    const field = document.body.querySelector<HTMLTextAreaElement>('textarea')!
    await type(field as unknown as HTMLInputElement, 'Still broken')
    field.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
    expect(props.onSend).not.toHaveBeenCalled()
    field.dispatchEvent(
      new KeyboardEvent('keydown', { key: 'Enter', ctrlKey: true, bubbles: true }),
    )
    expect(props.onSend).toHaveBeenCalledWith('Still broken')
  })

  it('lets IT start work on an open report or resolve it', async () => {
    const props = await conversation(makeIssue({ status: 'open' }), 'it')
    expect(hasButton('Reopen')).toBe(false)
    await type(document.body.querySelector<HTMLInputElement>('textarea')!, 'Ordering a fan.')
    await click('Start working on it')
    expect(props.onStatus).toHaveBeenCalledWith('in_progress', 'Ordering a fan.')
    await click('Mark as resolved')
    expect(props.onStatus).toHaveBeenLastCalledWith('resolved', 'Ordering a fan.')
  })

  it('lets IT reopen a resolved report', async () => {
    const props = await conversation(makeIssue({ status: 'resolved' }), 'it')
    expect(hasButton('Mark as resolved')).toBe(false)
    expect(hasButton('Start working on it')).toBe(false)
    await click('Reopen')
    expect(props.onStatus).toHaveBeenCalledWith('open', '')
  })

  it('only lets the reporter mark the report resolved', async () => {
    await conversation(makeIssue({ status: 'in_progress' }), 'reporter')
    expect(hasButton('Mark as resolved')).toBe(true)
    expect(hasButton('Start working on it')).toBe(false)
    expect(hasButton('Reopen')).toBe(false)
  })

  it('gives the reporter no status action once resolved', async () => {
    await conversation(makeIssue({ status: 'resolved' }), 'reporter')
    expect(hasButton('Reopen')).toBe(false)
    expect(hasButton('Mark as resolved')).toBe(false)
    expect(hasButton('Send')).toBe(true)
  })

  it('shows read-only roles the conversation without the field', async () => {
    await conversation(ISSUE, 'it', false)
    expect(items()).toHaveLength(5)
    expect(document.body.querySelector('textarea')).toBeNull()
    expect(hasButton('Send')).toBe(false)
  })
})

describe('IssueDetailView', () => {
  beforeEach(() => {
    stubPickers()
    vi.spyOn(portalApi, 'menuCounts').mockResolvedValue({} as Schemas['MenuCountsOut'])
  })

  async function show(
    viewer: 'reporter' | 'it',
    issue = makeIssue(),
    permissions: Record<string, 'read' | 'write'> = { issues: 'write' },
  ) {
    vi.spyOn(issuesApi, 'get').mockResolvedValue(issue)
    vi.spyOn(portalApi, 'myIssue').mockResolvedValue(issue)
    const result = await mountPage(IssueDetailView, { id: issue.id, viewer }, { permissions })
    unmount = () => result.wrapper.unmount()
    return result
  }

  const textarea = () => document.body.querySelector<HTMLInputElement>('textarea')!

  it('loads the report from the IT side for IT', async () => {
    await show('it')
    expect(issuesApi.get).toHaveBeenCalledWith('i1')
    expect(portalApi.myIssue).not.toHaveBeenCalled()
    expect(bodyText()).toContain('Not working: Dell Latitude 5450')
  })

  it("loads the reporter's own report in the portal and marks updates seen", async () => {
    await show('reporter')
    expect(portalApi.myIssue).toHaveBeenCalledWith('i1')
    expect(issuesApi.get).not.toHaveBeenCalled()
    expect(portalApi.menuCounts).toHaveBeenCalled()
  })

  it('sends IT messages and clears the field once sent', async () => {
    const answered = makeIssue({ entries: [message('m1', 'it', 'Bring it by, please.')] })
    const send = vi.spyOn(issuesApi, 'message').mockResolvedValue(answered)
    await show('it')
    await type(textarea(), 'Bring it by, please.')
    await click('Send')
    expect(send).toHaveBeenCalledWith('i1', 'Bring it by, please.')
    expect(bodyText()).toContain('Message sent')
    expect(document.body.querySelector('.message.mine')!.textContent).toContain(
      'Bring it by, please.',
    )
    expect(textarea().value).toBe('')
  })

  it('keeps the draft when sending fails', async () => {
    vi.spyOn(issuesApi, 'message').mockRejectedValue(new ApiError(503, 'Try again later.'))
    await show('it')
    await type(textarea(), 'Bring it by, please.')
    await click('Send')
    expect(bodyText()).toContain('Try again later.')
    expect(textarea().value).toBe('Bring it by, please.')
  })

  it('sends the reporter messages through the portal', async () => {
    const send = vi.spyOn(portalApi, 'myIssueMessage').mockResolvedValue(makeIssue())
    await show('reporter')
    await type(textarea(), 'It got worse.')
    await click('Send')
    expect(send).toHaveBeenCalledWith('i1', 'It got worse.')
  })

  it('changes the status with the typed message sent along', async () => {
    const update = vi
      .spyOn(issuesApi, 'update')
      .mockResolvedValue(
        makeIssue({ status: 'in_progress', entries: [statusChange('s1', 'in_progress')] }),
      )
    await show('it')
    await type(textarea(), 'Fan is ordered.')
    await click('Start working on it')
    expect(update).toHaveBeenCalledWith('i1', { status: 'in_progress', message: 'Fan is ordered.' })
    expect(bodyText()).toContain('Ian Tech started working on the report')
    expect(textarea().value).toBe('')
    // A report in work no longer counts as new in the menu.
    expect(portalApi.menuCounts).toHaveBeenCalled()
  })

  it('lets the reporter resolve the report through the portal', async () => {
    const resolve = vi
      .spyOn(portalApi, 'resolveMyIssue')
      .mockResolvedValue(makeIssue({ status: 'resolved' }))
    await show('reporter', makeIssue({ status: 'in_progress' }))
    await type(textarea(), 'Works again, thanks!')
    await click('Mark as resolved')
    expect(resolve).toHaveBeenCalledWith('i1', 'Works again, thanks!')
    expect(hasButton('Mark as resolved')).toBe(false)
  })

  it('shows IT without write rights the conversation only', async () => {
    await show('it', makeIssue(), { issues: 'read' })
    expect(bodyText()).toContain('The fan is very loud.')
    expect(document.body.querySelector('textarea')).toBeNull()
  })

  it('shows IT where the device is and who reported it', async () => {
    await show('it')
    expect(bodyText()).toContain('nb-0042')
    expect(bodyText()).toContain('HQ / Main office')
    expect(bodyText()).toContain('rita@example.com')
  })

  it('keeps internal device details and contact data from the reporter', async () => {
    await show('reporter')
    expect(bodyText()).toContain('SN-1')
    expect(bodyText()).not.toContain('nb-0042')
    expect(bodyText()).not.toContain('HQ / Main office')
    expect(bodyText()).not.toContain('rita@example.com')
  })

  it('tells the reporter when the device was returned since', async () => {
    await show('reporter', makeIssue({ still_assigned: false }))
    expect(bodyText()).toContain('The device has been returned since.')
    expect(bodyText()).not.toContain('Open device')
  })
})

describe('IssueListView', () => {
  beforeEach(() => {
    stubPickers()
  })

  async function show() {
    const result = await mountPage(IssueListView, {}, { permissions: { issues: 'write' } })
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('shows open reports by default and all once unticked', async () => {
    const list = vi.spyOn(issuesApi, 'list').mockResolvedValue(page([]))
    await show()
    expect(list).toHaveBeenCalledWith(
      expect.objectContaining({ status: ['open', 'in_progress'], ordering: '-created_at' }),
    )
    await check('Open only')
    expect(list).toHaveBeenLastCalledWith(expect.objectContaining({ status: [] }))
  })

  it('opens a report from its row', async () => {
    vi.spyOn(issuesApi, 'list').mockResolvedValue(
      page([
        {
          ...makeIssue({ id: 'i5' }),
          asset: { id: 'a1', inventory_number: 'NB-0042', model: modelRef() },
          last_message: null,
        } as unknown as Schemas['AssetIssueOut'],
      ]),
    )
    const { router } = await show()
    const row = document.body.querySelector<HTMLElement>('tbody tr')!
    expect(row.textContent).toContain('NB-0042')
    expect(row.textContent).toContain('Rita Reporter')
    row.click()
    await flushPromises()
    expect(router.currentRoute.value.fullPath).toBe('/issue/i5')
  })
})
