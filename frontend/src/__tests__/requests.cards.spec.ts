import { flushPromises } from '@vue/test-utils'
import { NSelect } from 'naive-ui'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import AssignmentCard from '@/components/requests/AssignmentCard.vue'
import HandoverCard from '@/components/requests/HandoverCard.vue'
import RequestSteps from '@/components/requests/RequestSteps.vue'
import ReturnsCard from '@/components/requests/ReturnsCard.vue'
import ApprovalCard from '@/components/requests/detail/ApprovalCard.vue'
import HandoverPlanCard from '@/components/requests/detail/HandoverPlanCard.vue'
import RequestInfoCard from '@/components/requests/detail/RequestInfoCard.vue'

import {
  IT_MAX,
  JANE,
  REQUEST_ID,
  allocatedRequest,
  device,
  lentRequest,
  makeItem,
  makeRequest,
  mountWithApp,
  screen,
  user,
} from './requestsHelpers'

type AssetRequest = Schemas['AssetRequestOut']

const api = vi.hoisted(() => ({ assign: vi.fn<(...args: never[]) => Promise<unknown>>() }))

vi.mock('@/api/requests', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/requests')>()),
  requestsApi: { assign: api.assign },
}))
vi.mock('@/api/accounts', async (importOriginal) => {
  const empty = { list: async () => ({ items: [], count: 0 }) }
  return {
    ...(await importOriginal<typeof import('@/api/accounts')>()),
    usersApi: empty,
    teamsApi: { ...empty, get: async () => ({ members: [] }) },
  }
})

/** Label → value of the cards' detail grids. */
const details = () =>
  Object.fromEntries(
    [...document.body.querySelectorAll('.n-card dt')].map((label) => [
      label.textContent!.trim(),
      label.nextElementSibling?.textContent?.replace(/\s+/g, ' ').trim(),
    ]),
  )

describe('request detail cards', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    api.assign.mockReset()
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
  })

  async function card(
    component: Parameters<typeof mountWithApp>[0],
    assetRequest: AssetRequest,
    props: Record<string, unknown> = {},
  ) {
    const result = await mountWithApp(component, { assetRequest, ...props })
    unmount = () => result.wrapper.unmount()
    return result
  }

  describe('the planned handover', () => {
    it('says the request waits at the terminal, and that the check is skipped', async () => {
      await card(
        HandoverPlanCard,
        allocatedRequest({ status: 'ready', skip_device_check: true, prepared_by: IT_MAX }),
      )
      expect(screen()).toContain('Pickup with signature · without device check')
      expect(screen()).toContain(
        'Can be completed at the pickup terminal. The device check is skipped.',
      )
      expect(screen()).toContain('Max IT')
    })

    it('reminds IT to record a simple pickup afterwards', async () => {
      await card(HandoverPlanCard, allocatedRequest({ status: 'ready', handover_mode: 'collect' }))
      expect(screen()).toContain('Afterwards record under “Hand out” who received them.')
    })

    it('keeps IT’s notes from the employee', async () => {
      await card(HandoverPlanCard, allocatedRequest({ status: 'ready', prepared_by: IT_MAX }), {
        forEmployee: true,
      })
      expect(screen()).not.toContain('pickup terminal')
      expect(screen()).not.toContain('Max IT')
    })
  })

  describe('the handover', () => {
    it('shows who received the devices and the notes per device', async () => {
      const request = lentRequest()
      request.items[0]!.allocations[0]!.handout_note = 'Scratch on the lid'
      await card(HandoverCard, request)
      expect(screen()).toContain('Handed out by IT')
      expect(screen()).toContain('INV-001 Scratch on the lid')
      expect(screen()).toContain('Handover record')
    })

    it('shows the signature given at the terminal', async () => {
      const request = lentRequest()
      request.handover = {
        ...request.handover!,
        method: 'signature',
        signature: 'data:image/png;base64,AA',
      }
      await card(HandoverCard, request)
      expect(document.body.querySelector('figure img')!.getAttribute('src')).toBe(
        'data:image/png;base64,AA',
      )
      expect(screen()).toContain('Signature · Jane Doe')
    })
  })

  describe('the returns', () => {
    it('shows the due date as overdue and the last reminder', async () => {
      await card(
        ReturnsCard,
        lentRequest({ is_overdue: true, reminded_at: '2026-11-07T09:30:00Z', reminded_by: IT_MAX }),
        { withDue: true },
      )
      expect(screen()).toContain('11/06/2026 · overdue')
      expect(screen()).toContain('Max IT')
      // Nothing came back yet: no record to print.
      expect(screen()).not.toContain('Handover record')
    })

    it('lists what came back with each return', async () => {
      const request = lentRequest({
        returns: [
          {
            id: 'ret-1',
            returned_at: '2026-11-06T15:00:00Z',
            returned_by: IT_MAX,
            notes: 'In the bag.',
          },
        ],
      })
      request.items = [
        makeItem({
          quantity_confirmed: 2,
          quantity_requested: 2,
          allocations: [
            device('INV-001', 'Laptop 14', {
              device_return: 'ret-1',
              returned_damaged: true,
              return_note: 'Cracked',
            }),
            device('INV-002', 'Laptop 14'),
          ],
        }),
      ]
      await card(ReturnsCard, request)
      const returned = [...document.body.querySelectorAll('.return li')].map((li) =>
        [...li.querySelectorAll('span')].map((s) => s.textContent),
      )
      expect(returned).toEqual([['INV-001', 'Acme Laptop 14', 'Damaged', 'Cracked']])
      expect(screen()).toContain('In the bag.')
      expect(screen()).toContain('Handover record')
    })
  })

  describe('the approval', () => {
    it('names who may still approve', async () => {
      await card(
        ApprovalCard,
        makeRequest({ approval: 'pending', approvers: [user('Ann Boss'), user('Bob Head')] }),
      )
      expect(screen()).toContain('Ann Boss, Bob Head')
    })

    it('marks an approval the requester gave themselves', async () => {
      await card(
        ApprovalCard,
        makeRequest({
          approval: 'approved',
          approver: JANE,
          approval_decided_at: '2026-10-01T09:00:00Z',
          approval_comment: 'Needed for the fair.',
        }),
      )
      expect(screen()).toContain('Jane Doe · as approver themselves')
      expect(screen()).toContain('Needed for the fair.')
    })
  })

  describe('the request info', () => {
    it('names who recorded it for the employee and the request it follows', async () => {
      await card(
        RequestInfoCard,
        makeRequest({
          created_by: IT_MAX,
          origin: 'direct',
          follows: {
            id: 'r0',
            number: 'R-2026-0007',
            status: 'rejected',
            approval: '',
            approval_comment: '',
            it_comment: '',
          },
          it_comment: 'Take the black bag.',
        }),
      )
      expect(details()).toMatchObject({
        'Requested by': 'Jane Doe',
        'Recorded by': 'Max IT',
        Follows: 'R-2026-0007 · Rejected',
        Origin: 'Direct hand-out',
        'Comment from IT': 'Take the black bag.',
      })
    })

    it('does not repeat the requester as the one who recorded it', async () => {
      await card(RequestInfoCard, makeRequest())
      expect(details()).not.toHaveProperty('Recorded by')
      expect(details()['Period']).toBe('11/02/2026 → 11/06/2026')
    })
  })

  describe('the steps', () => {
    const steps = () =>
      [...document.body.querySelectorAll('.n-step')].map((s) => ({
        title: s.querySelector('.n-step-content-header__title')!.textContent!.trim(),
        current: s.classList.contains('n-step--process-status'),
      }))

    it('starts with the approval when the department had to approve', async () => {
      await card(RequestSteps, makeRequest({ approval: 'pending', status: 'pending_approval' }))
      expect(steps().map((s) => s.title)).toEqual([
        'Approval',
        'Submitted',
        'Confirmed',
        'Ready for pickup',
        'Handed out',
        'Completed',
      ])
      expect(steps().find((s) => s.current)?.title).toBe('Approval')
    })

    it('ends with the hand-out for a permanent request', async () => {
      await card(RequestSteps, makeRequest({ duration: 'permanent', status: 'confirmed' }))
      expect(steps().map((s) => s.title)).toEqual([
        'Submitted',
        'Confirmed',
        'Ready for pickup',
        'Handed out',
      ])
      expect(steps().find((s) => s.current)?.title).toBe('Confirmed')
    })
  })

  describe('the assignment', () => {
    it('assigns the request to the current IT member', async () => {
      const updated = makeRequest({ assignee: IT_MAX })
      api.assign.mockResolvedValue(updated)
      const onUpdated = vi.fn<(r: Schemas['AssetRequestOut']) => void>()
      await card(AssignmentCard, makeRequest(), { onUpdated })

      document.body.querySelector<HTMLButtonElement>('.assignee-label button')!.click()
      await flushPromises()
      expect(api.assign).toHaveBeenCalledWith(REQUEST_ID, { team: null, assignee: IT_MAX.id })
      expect(onUpdated).toHaveBeenCalledWith(updated)
    })

    it('saves team and person together with the save button', async () => {
      const updated = makeRequest({
        assigned_team: { id: 'team-1', code: 'support', name: 'IT-Support' },
        assignee: JANE,
      })
      api.assign.mockResolvedValue(updated)
      const onUpdated = vi.fn<(r: Schemas['AssetRequestOut']) => void>()
      const { wrapper } = await card(AssignmentCard, makeRequest(), { onUpdated })
      const save = () =>
        document.body.querySelector<HTMLButtonElement>('.n-card-header__extra button')!
      expect(save().disabled).toBe(true)

      const [team, person] = wrapper.findAllComponents(EntitySelect)
      team!.findComponent(NSelect).vm.$emit('update:value', 'team-1')
      person!.findComponent(NSelect).vm.$emit('update:value', JANE.id)
      await flushPromises()
      expect(api.assign).not.toHaveBeenCalled()
      expect(save().disabled).toBe(false)

      save().click()
      await flushPromises()
      expect(api.assign).toHaveBeenCalledTimes(1)
      expect(api.assign).toHaveBeenCalledWith(REQUEST_ID, { team: 'team-1', assignee: JANE.id })
      expect(onUpdated).toHaveBeenCalledWith(updated)
    })

    it('shows why the assignment failed', async () => {
      api.assign.mockRejectedValue(new ApiError(403, 'Not allowed.'))
      await card(AssignmentCard, makeRequest())
      document.body.querySelector<HTMLButtonElement>('.assignee-label button')!.click()
      await flushPromises()
      expect(screen()).toContain('Not allowed.')
    })
  })
})
