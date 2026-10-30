import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import ApprovalDetailView from '@/views/portal/ApprovalDetailView.vue'
import ApprovalsView from '@/views/portal/ApprovalsView.vue'

import { makeUser } from './helpers'
import { button, click, hasButton, typeInto } from './dom'
import { assetRequest, bodyText, mountPage, requestListItem, unmountPages } from './portalHelpers'

const api = vi.hoisted(() => ({
  list: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  approve: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  decline: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  get: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
}))

vi.mock('@/api/requests', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/api/requests')>()
  return {
    ...original,
    approvalsApi: { list: api.list, approve: api.approve, decline: api.decline },
    requestsApi: { ...original.requestsApi, get: api.get },
  }
})

const APPROVER = makeUser({ id: 'u-boss', display_name: 'Bob Boss', is_approver: true })

describe('ApprovalsView', () => {
  beforeEach(() => Object.values(api).forEach((mock) => mock.mockReset()))
  afterEach(unmountPages)

  it('lists the waiting requests with requester, department and purpose', async () => {
    api.list.mockResolvedValue({
      items: [requestListItem({ id: 'r7', number: 'R-7', summary: '2× Headset' })],
      count: 1,
    })
    await mountPage(ApprovalsView, { user: APPROVER })
    const row = document.body.querySelector('tbody tr')!.textContent
    expect(row).toContain('R-7')
    expect(row).toContain('Jane Doe')
    expect(row).toContain('Sales')
    expect(row).toContain('Workshop in Munich')
    expect(row).toContain('2× Headset')
  })

  it('opens a request from its row', async () => {
    api.list.mockResolvedValue({ items: [requestListItem({ id: 'r7' })], count: 1 })
    const { router } = await mountPage(ApprovalsView, { user: APPROVER })
    await click(document.body.querySelector('tbody tr')!)
    expect(router.currentRoute.value.name).toBe('portal-approval')
    expect(router.currentRoute.value.params.id).toBe('r7')
  })

  it('says when nothing is waiting', async () => {
    api.list.mockResolvedValue({ items: [], count: 0 })
    await mountPage(ApprovalsView, { user: APPROVER })
    expect(bodyText()).toContain('No request is waiting for your approval.')
  })
})

describe('ApprovalDetailView', () => {
  beforeEach(() => Object.values(api).forEach((mock) => mock.mockReset()))
  afterEach(unmountPages)

  const waiting = (overrides: Partial<Schemas['AssetRequestOut']> = {}) =>
    assetRequest({
      status: 'pending_approval',
      approval: 'pending',
      can_approve: true,
      ...overrides,
    })

  async function open(request = waiting()) {
    api.get.mockResolvedValue(request)
    return mountPage(ApprovalDetailView, {
      props: { id: request.id },
      url: `/portal/approvals/${request.id}`,
      user: APPROVER,
    })
  }

  const comment = () => document.body.querySelector<HTMLTextAreaElement>('.n-modal textarea')!

  it('approves with an optional comment and goes back to the list', async () => {
    api.approve.mockResolvedValue(waiting({ approval: 'approved', status: 'submitted' }))
    const { router } = await open()
    await click(button('Approve'))
    expect(bodyText()).toContain('The request is then forwarded to IT.')
    await typeInto(comment(), 'Budget is fine')
    await click(button('Approve'))

    expect(api.approve).toHaveBeenCalledWith('r1', 'Budget is fine')
    expect(bodyText()).toContain('Approved and forwarded to IT')
    expect(router.currentRoute.value.name).toBe('portal-approvals')
  })

  it('approves without a comment', async () => {
    api.approve.mockResolvedValue(waiting({ approval: 'approved' }))
    await open()
    await click(button('Approve'))
    await click(button('Approve'))
    expect(api.approve).toHaveBeenCalledWith('r1', '')
  })

  it('needs a reason to decline', async () => {
    api.decline.mockResolvedValue(waiting({ approval: 'rejected', status: 'rejected' }))
    const { router } = await open()
    await click(button('Decline'))
    expect(button('Decline').disabled).toBe(true)
    await typeInto(comment(), '  ')
    expect(button('Decline').disabled).toBe(true)
    await typeInto(comment(), 'No budget left this year')
    await click(button('Decline'))

    expect(api.decline).toHaveBeenCalledWith('r1', 'No budget left this year')
    expect(api.approve).not.toHaveBeenCalled()
    expect(bodyText()).toContain('Request declined')
    expect(router.currentRoute.value.name).toBe('portal-approvals')
  })

  it('starts each decision with an empty comment', async () => {
    await open()
    await click(button('Decline'))
    await typeInto(comment(), 'Draft reason')
    await click(button('Cancel'))
    await click(button('Approve'))
    expect(comment().value).toBe('')
  })

  it('keeps the dialog open with the comment when the decision fails', async () => {
    api.approve.mockRejectedValue(new ApiError(409, 'Already decided by Alice.'))
    const { router } = await open()
    await click(button('Approve'))
    await typeInto(comment(), 'OK')
    await click(button('Approve'))
    expect(bodyText()).toContain('Already decided by Alice.')
    expect(comment().value).toBe('OK')
    expect(router.currentRoute.value.name).not.toBe('portal-approvals')
  })

  it('offers no decision when the approver may not decide', async () => {
    await open(waiting({ can_approve: false, approval: 'approved' }))
    expect(hasButton('Approve')).toBe(false)
    expect(hasButton('Decline')).toBe(false)
  })

  const followingRejected = () =>
    waiting({
      follows: {
        id: 'r0',
        number: 'R-2026-0001',
        status: 'rejected',
        approval: 'rejected',
        approval_comment: 'Too expensive',
        it_comment: 'IT would have had one',
      },
    })

  it('points out an earlier request and the department’s reason it ended', async () => {
    await open(followingRejected())
    const alert = document.body.querySelector('.n-alert')!.textContent
    expect(alert).toContain('Requested again after R-2026-0001')
    expect(alert).toMatch(/Rejected\s*: „Too expensive“/)
    expect(alert).not.toContain('IT would have had one')
  })

  it('writes the reason right after the status, without a space before the colon', async () => {
    await open(followingRejected())
    expect(document.body.querySelector('.n-alert')!.textContent).toContain(
      'Rejected: „Too expensive“',
    )
  })
})
