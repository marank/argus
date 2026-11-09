import { flushPromises, mount } from '@vue/test-utils'
import { NDialogProvider, NMessageProvider } from 'naive-ui'
import { createPinia, setActivePinia } from 'pinia'
import { defineComponent, h, type Component } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import type { Schemas } from '@/api/types'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

import { makeUser } from './helpers'
import { shown } from './dom'

type AssetRequest = Schemas['AssetRequestOut']
type Item = Schemas['AssetRequestItemOut']
type Allocation = Schemas['AllocationOut']
type Event = Schemas['AssetRequestEventOut']

export const REQUEST_ID = '11111111-1111-1111-1111-111111111111'

export const user = (name: string, id = name.toLowerCase()): Schemas['UserRefOut'] => ({
  id,
  username: id,
  display_name: name,
})

export const JANE = user('Jane Doe', 'jane')
export const IT_MAX = user('Max IT', 'max')

const model = (name: string): Schemas['AssetModelRefOut'] => ({
  id: `model-${name}`,
  name,
  designation: name,
  full_name: `Acme ${name}`,
  tracking: 'serialized',
})

export const LAPTOP_CATEGORY: Schemas['CategoryRefOut'] = {
  identifier_label: '',
  device_naming: 'none',
  id: 'cat-laptop',
  code: 'LAP',
  icon: 'laptop',
  item_name: 'Laptop',
  kind: 'hardware',
  name: 'Laptops',
}

export function makeAllocation(overrides: Partial<Allocation> = {}): Allocation {
  return {
    id: 'alloc-1',
    allocated_at: '2026-10-01T09:00:00Z',
    allocated_by: IT_MAX,
    asset: null,
    category_icon: 'laptop',
    consumable: null,
    device_return: null,
    handed_out_at: null,
    handout_note: '',
    license: null,
    quantity: 1,
    return_note: '',
    returned_at: null,
    returned_damaged: false,
    ...overrides,
  }
}

/** An allocated device, e.g. `device('INV-001', 'Laptop 14')`. */
export function device(
  inventoryNumber: string,
  modelName: string,
  overrides: Partial<Allocation> = {},
): Allocation {
  return makeAllocation({
    id: `alloc-${inventoryNumber}`,
    asset: {
      id: `asset-${inventoryNumber}`,
      inventory_number: inventoryNumber,
      name: '',
      model: model(modelName),
      serial_number: `SN-${inventoryNumber}`,
      status: 'reserved',
    },
    ...overrides,
  })
}

/** A license seat for the employee personally. */
export function seat(modelName: string, overrides: Partial<Allocation> = {}): Allocation {
  return makeAllocation({
    id: `alloc-seat-${modelName}`,
    license: {
      id: 'lic-1',
      model: model(modelName),
      device: null,
      reference: '',
      valid_until: null,
    },
    ...overrides,
  })
}

export function makeItem(overrides: Partial<Item> = {}): Item {
  const allocations = overrides.allocations ?? []
  const requested = overrides.quantity_requested ?? 1
  const confirmed = overrides.quantity_confirmed === undefined ? null : overrides.quantity_confirmed
  const allocated = allocations.reduce((sum, a) => sum + a.quantity, 0)
  return {
    id: 'item-1',
    allocations,
    asset_model: model('Laptop 14'),
    category: LAPTOP_CATEGORY,
    description: '',
    is_free_text: false,
    is_software: false,
    label: 'Acme Laptop 14',
    note: '',
    quantity_requested: requested,
    quantity_confirmed: confirmed,
    quantity_allocated: allocated,
    quantity_missing: Math.max((confirmed ?? requested) - allocated, 0),
    ...overrides,
  }
}

export function makeRequest(overrides: Partial<AssetRequest> = {}): AssetRequest {
  return {
    id: REQUEST_ID,
    number: 'R-2026-0042',
    title: 'Training in Munich',
    status: 'submitted',
    approval: '',
    approval_comment: '',
    approval_decided_at: null,
    approver: null,
    approvers: [],
    assigned_team: null,
    assignee: null,
    can_approve: false,
    completed_at: null,
    confirmed_at: null,
    created_at: '2026-10-01T08:00:00Z',
    created_by: JANE,
    department: { id: 'dep-1', name: 'Sales' },
    duration: 'temporary',
    start_date: '2026-11-02',
    end_date: '2026-11-06',
    events: [],
    follows: null,
    handed_out_at: null,
    handled_by: null,
    handover: null,
    handover_mode: 'pickup',
    is_overdue: false,
    it_comment: '',
    item_count: 1,
    items: [makeItem()],
    notes: '',
    origin: 'request',
    pickup_at: null,
    pickup_location: null,
    prepared_by: null,
    reminded_at: null,
    reminded_by: null,
    requested_pickup_date: null,
    requester: JANE,
    returns: [],
    skip_device_check: false,
    summary: '1× Acme Laptop 14',
    unit_count: 1,
    ...overrides,
  }
}

/** Confirmed and fully allocated: the next step is marking it ready. */
export const allocatedRequest = (overrides: Partial<AssetRequest> = {}) =>
  makeRequest({
    status: 'confirmed',
    items: [makeItem({ quantity_confirmed: 1, allocations: [device('INV-001', 'Laptop 14')] })],
    ...overrides,
  })

/** Two laptops on loan to Jane until Nov 6. */
export const lentRequest = (overrides: Partial<AssetRequest> = {}) =>
  makeRequest({
    status: 'handed_out',
    handed_out_at: '2026-11-02T09:00:00Z',
    items: [
      makeItem({
        quantity_requested: 2,
        quantity_confirmed: 2,
        allocations: [
          device('INV-001', 'Laptop 14', { handed_out_at: '2026-11-02T09:00:00Z' }),
          device('INV-002', 'Laptop 14', { handed_out_at: '2026-11-02T09:00:00Z' }),
        ],
      }),
    ],
    handover: {
      handed_out_at: '2026-11-02T09:00:00Z',
      handed_out_by: IT_MAX,
      recorded_by: IT_MAX,
      method: 'direct',
      received_by: JANE,
      received_by_name: 'Jane Doe',
      location: '',
      notes: '',
      signature: '',
    },
    ...overrides,
  })

/** The `data` of the history entries of kind `K`. */
type DataOf<K, E = Event> = E extends { kind: infer EK; data: infer D }
  ? K extends EK
    ? D
    : never
  : never

/** A history entry; `data` must match the kind's shape. */
export function event<K extends Event['kind']>(
  kind: K,
  data: DataOf<K>,
  overrides: Partial<Omit<Event, 'kind' | 'data'>> = {},
): Event {
  return {
    id: `ev-${kind}-${Math.random()}`,
    at: '2026-10-02T10:00:00Z',
    actor: IT_MAX,
    kind,
    data,
    ...overrides,
  } as Event
}

/**
 * Mounts a page or component the way the app does: Naive UI's message and dialog
 * providers, i18n, Pinia and a router, signed in with the given rights on requests.
 */
export async function mountWithApp(
  component: Component,
  props: Record<string, unknown> = {},
  { permission = 'write' as 'read' | 'write' | null, url = '/' } = {},
) {
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().user = makeUser({
    id: IT_MAX.id,
    is_it_staff: true,
    permissions: permission ? { requests: permission } : {},
  })
  const page = { render: () => null }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: page },
      { path: '/requests/:id', name: 'request', component: page },
      { path: '/requests/:id/protocol', name: 'handover-protocol', component: page },
      { path: '/portal/new', name: 'portal-new', component: page },
      { path: '/assets/:id', name: 'asset', component: page },
      { path: '/licenses/:id', name: 'license', component: page },
      { path: '/licenses', name: 'licenses', component: page },
    ],
  })
  await router.push(url)
  const wrapper = mount(
    defineComponent({
      render: () =>
        h(NMessageProvider, null, {
          default: () => h(NDialogProvider, null, { default: () => h(component, props) }),
        }),
    }),
    { attachTo: document.body, global: { plugins: [i18n, pinia, router] } },
  )
  await flushPromises()
  return { wrapper, router }
}

/** Everything on screen, including teleported modals, dialogs and toasts. */
export const screen = () => document.body.textContent ?? ''

/**
 * Closed modals and dialogs stay in the DOM with `display: none` in jsdom (their
 * leave transition never ends), so only what is not hidden counts as shown.
 */
/** The open modal card or dialog (Naive UI teleports it to the end of the body), if any. */
export const modal = () =>
  [...document.body.querySelectorAll<HTMLElement>('.n-modal')].filter(shown).at(-1) ?? null

/** The open modal; fails the test when none is open. */
export function openModal(): HTMLElement {
  const found = modal()
  if (!found) throw new Error('no modal is open')
  return found
}
