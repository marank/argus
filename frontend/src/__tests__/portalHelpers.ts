import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { NDialogProvider, NMessageProvider } from 'naive-ui'
import { createPinia, setActivePinia } from 'pinia'
import { vi } from 'vitest'
import { defineComponent, h, type Component } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import type { Schemas } from '@/api/types'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'

import { makeSiteSettings, makeUser } from './helpers'

/** The named routes the portal and terminal pages link to; the pages themselves are not rendered. */
const page = { render: () => null }
const ROUTES = [
  { path: '/', name: 'dashboard', component: page },
  { path: '/portal/new', name: 'portal-new', component: page },
  { path: '/portal/requests', name: 'portal-requests', component: page },
  { path: '/portal/requests/:id', name: 'portal-request', component: page },
  { path: '/portal/approvals', name: 'portal-approvals', component: page },
  { path: '/portal/approvals/:id', name: 'portal-approval', component: page },
  { path: '/portal/devices/:id', name: 'portal-device', component: page },
  { path: '/portal/issues/:id', name: 'portal-issue', component: page },
  { path: '/requests/:id', name: 'request', component: page },
  { path: '/terminal', name: 'terminal', component: page },
  { path: '/terminal/:id', name: 'terminal-pickup', component: page },
]

const mounted: VueWrapper[] = []

/**
 * Mounts a page with the real providers (messages, dialogs), i18n, Pinia and a router
 * at `url`, signed in as `user`. `flags` switches site features off.
 */
export async function mountPage(
  component: Component,
  options: {
    props?: Record<string, unknown>
    url?: string
    user?: Schemas['CurrentUserOut']
    flags?: Record<string, boolean>
  } = {},
) {
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().user = options.user ?? makeUser()
  if (options.flags) useFeaturesStore().settings = makeSiteSettings(options.flags)
  const router = createRouter({ history: createMemoryHistory(), routes: ROUTES })
  await router.push(options.url ?? '/')
  const wrapper = mount(
    defineComponent({
      render: () =>
        h(NMessageProvider, null, {
          default: () =>
            h(NDialogProvider, null, { default: () => h(component, options.props ?? {}) }),
        }),
    }),
    { attachTo: document.body, global: { plugins: [i18n, pinia, router] } },
  )
  mounted.push(wrapper)
  await flushPromises()
  return { wrapper, router }
}

/** Call in afterEach: unmounts the pages and clears what Naive UI teleported to the body. */
export function unmountPages() {
  mounted.splice(0).forEach((wrapper) => wrapper.unmount())
  document.body.innerHTML = ''
  localStorage.clear()
}

/** All visible text, including modals and messages teleported to the body. */
export const bodyText = () => document.body.textContent ?? ''

/** The input or textarea showing this placeholder. */
export function field(placeholder: string): HTMLInputElement {
  const input = document.body.querySelector<HTMLInputElement>(`[placeholder="${placeholder}"]`)
  if (!input) throw new Error(`no field "${placeholder}"`)
  return input
}

/**
 * jsdom has no canvas: a 2D context that accepts the drawing calls, a fixed PNG
 * export and pointer capture are enough to sign on the SignaturePad.
 */
export const SIGNATURE = 'data:image/png;base64,c2lnbmVk'
export function stubCanvas() {
  const context = new Proxy({}, { get: () => () => {}, set: () => true })
  vi.spyOn(HTMLCanvasElement.prototype, 'getContext').mockReturnValue(
    context as unknown as CanvasRenderingContext2D,
  )
  vi.spyOn(HTMLCanvasElement.prototype, 'toDataURL').mockReturnValue(SIGNATURE)
  Element.prototype.setPointerCapture ??= () => {}
}

/** A stroke on the canvas: press, move, release. */
export async function drawOn(canvas: Element) {
  for (const [type, x] of [
    ['pointerdown', 10],
    ['pointermove', 40],
    ['pointerup', 40],
  ] as const) {
    canvas.dispatchEvent(new MouseEvent(type, { clientX: x, clientY: 20, bubbles: true }))
  }
  await flushPromises()
}

// ---- Fixtures, typed with the API's schemas so they break when it changes. ----

const ref = (id: string, name: string) => ({ id, display_name: name, username: name.toLowerCase() })

export function catalogModel(
  overrides: Partial<Schemas['CatalogModelOut']> & Pick<Schemas['CatalogModelOut'], 'id'>,
): Schemas['CatalogModelOut'] {
  const name = overrides.full_name ?? `Model ${overrides.id}`
  return {
    name,
    full_name: name,
    description: '',
    tracking: 'serialized',
    available: null,
    reserved: null,
    accessories: [],
    ...overrides,
  }
}

export function catalogCategory(
  overrides: Partial<Schemas['CatalogCategoryOut']> &
    Pick<Schemas['CatalogCategoryOut'], 'id' | 'name'>,
): Schemas['CatalogCategoryOut'] {
  return {
    code: overrides.id.toUpperCase(),
    description: '',
    icon: 'laptop',
    item_name: '',
    kind: 'hardware',
    parent_id: null,
    model_choice: 'any_or_specific',
    holds_accessories: false,
    models: [],
    available: null,
    reserved: null,
    ...overrides,
  }
}

const JANE = ref('u1', 'Jane Doe')

export function requestItem(
  overrides: Partial<Schemas['AssetRequestItemOut']> = {},
): Schemas['AssetRequestItemOut'] {
  return {
    id: 'i1',
    label: 'ThinkPad T14',
    category: null,
    asset_model: {
      id: 'm1',
      name: 'T14',
      full_name: 'ThinkPad T14',
      designation: '',
      tracking: 'serialized',
    },
    description: '',
    is_free_text: false,
    is_software: false,
    note: '',
    quantity_requested: 1,
    quantity_confirmed: null,
    quantity_allocated: 0,
    quantity_missing: 1,
    allocations: [],
    ...overrides,
  }
}

export function assetRequest(
  overrides: Partial<Schemas['AssetRequestOut']> = {},
): Schemas['AssetRequestOut'] {
  return {
    id: 'r1',
    number: 'R-2026-0042',
    title: 'Workshop in Munich',
    notes: '',
    summary: '1× ThinkPad T14',
    status: 'submitted',
    approval: '',
    approval_comment: '',
    approval_decided_at: null,
    approver: null,
    approvers: [],
    can_approve: false,
    assigned_team: null,
    assignee: null,
    completed_at: null,
    confirmed_at: null,
    created_at: '2026-10-01T09:00:00Z',
    created_by: JANE,
    department: { id: 'd1', name: 'Sales' },
    duration: 'temporary',
    start_date: '2026-10-20',
    end_date: '2026-10-24',
    events: [],
    follows: null,
    handed_out_at: null,
    handled_by: null,
    handover: null,
    handover_mode: 'pickup',
    is_overdue: false,
    it_comment: '',
    item_count: 1,
    unit_count: 1,
    items: [requestItem()],
    origin: 'request',
    pickup_at: null,
    pickup_location: null,
    prepared_by: null,
    reminded_at: null,
    reminded_by: null,
    requested_pickup_date: '2026-10-20',
    requester: JANE,
    returns: [],
    skip_device_check: false,
    ...overrides,
  }
}

export function requestListItem(
  overrides: Partial<Schemas['AssetRequestListOut']> = {},
): Schemas['AssetRequestListOut'] {
  const rest = assetRequest()
  return {
    id: rest.id,
    number: rest.number,
    title: rest.title,
    summary: rest.summary,
    status: rest.status,
    approval: rest.approval,
    assigned_team: rest.assigned_team,
    assignee: rest.assignee,
    created_at: rest.created_at,
    department: rest.department,
    duration: rest.duration,
    start_date: rest.start_date,
    end_date: rest.end_date,
    handover_mode: rest.handover_mode,
    is_overdue: rest.is_overdue,
    item_count: rest.item_count,
    unit_count: rest.unit_count,
    origin: rest.origin,
    pickup_at: rest.pickup_at,
    requested_pickup_date: rest.requested_pickup_date,
    requester: rest.requester,
    ...overrides,
  }
}
