import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { NDialogProvider, NMessageProvider, NSelect } from 'naive-ui'
import { createPinia, setActivePinia } from 'pinia'
import { vi } from 'vitest'
import { defineComponent, h, type Component } from 'vue'
import { createMemoryHistory, createRouter } from 'vue-router'

import { teamsApi, usersApi } from '@/api/accounts'
import { assetsApi, consumablesApi } from '@/api/inventory'
import { assetModelsApi, categoriesApi, locationsApi, suppliersApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'
import type { Page } from '@/types/common'

import { makeSiteSettings, makeUser } from './helpers'
import { fakeMatchMedia, hasButton } from './dom'

type Permissions = Record<string, 'read' | 'write'>

export const page = <T>(items: T[]): Page<T> => ({ items, count: items.length })

/**
 * The lists behind the pickers (models, locations, suppliers, users, …) answer
 * empty unless a test fills one; nothing reaches the network.
 */
export function stubPickers() {
  for (const api of [
    assetModelsApi,
    categoriesApi,
    locationsApi,
    suppliersApi,
    usersApi,
    teamsApi,
    assetsApi,
    consumablesApi,
  ] as { list: () => unknown }[])
    vi.spyOn(api, 'list').mockResolvedValue(page([]))
}

/**
 * Mounts `component` the way the app shows it: Naive UI's message and dialog
 * providers, i18n (English), Pinia with a signed-in IT user holding
 * `permissions`, and a router knowing the pages the views link to. Pass
 * `reactive` props to open and close modals from the test.
 */
export async function mountPage(
  component: Component,
  props: Record<string, unknown> = {},
  options: { permissions?: Permissions; flags?: Record<string, boolean>; url?: string } = {},
) {
  if (typeof window.matchMedia !== 'function') fakeMatchMedia()
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().user = makeUser({ is_it_staff: true, permissions: options.permissions ?? {} })
  useFeaturesStore().settings = makeSiteSettings(options.flags ?? {})
  const stub = { render: () => null }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/', component: stub },
      ...[
        'asset',
        'assets',
        'license',
        'licenses',
        'order',
        'orders',
        'request',
        'issue',
        'portal-new',
        'portal-device',
        'portal-issue',
      ].map((name) => ({ path: `/${name}/:id?`, name, component: stub })),
    ],
  })
  await router.push(options.url ?? '/')
  const wrapper = mount(
    defineComponent({
      render: () =>
        h(NMessageProvider, null, {
          default: () => h(NDialogProvider, null, { default: () => h(component, { ...props }) }),
        }),
    }),
    { attachTo: document.body, global: { plugins: [i18n, pinia, router] } },
  )
  await flushPromises()
  return { wrapper, router }
}

export const bodyText = () => document.body.textContent ?? ''

/** Whether the page header (not a closing modal) offers this action. */
export const headerHas = (text: string) =>
  hasButton(text, document.body.querySelector('.page-header') ?? document.body)

function formItem(label: string): Element {
  const items = [...document.body.querySelectorAll('.n-form-item')]
  const labelOf = (el: Element) => el.querySelector('.n-form-item-label')?.textContent?.trim() ?? ''
  // Required fields carry a star after the label.
  const item =
    items.filter((el) => labelOf(el).replace(/\s*\*$/, '') === label).at(-1) ??
    items.filter((el) => labelOf(el).startsWith(label)).at(-1)
  if (!item) throw new Error(`no field "${label}"`)
  return item
}

export function hasField(label: string) {
  try {
    formItem(label)
    return true
  } catch {
    return false
  }
}

/** The input (or textarea) of the form field with this label. */
export function field(label: string): HTMLInputElement {
  const input = formItem(label).querySelector<HTMLInputElement>('textarea, input')
  if (!input) throw new Error(`no input in field "${label}"`)
  return input
}

/**
 * The plain select (not a record picker) offering `option`. Naive UI's option
 * list is virtual and stays empty in jsdom, so the options are read from it.
 */
function plainSelect(wrapper: VueWrapper, option: string) {
  const inPickers = new Set(
    wrapper.findAllComponents(EntitySelect).map((s) => s.findComponent(NSelect).vm),
  )
  const select = wrapper
    .findAllComponents(NSelect)
    .filter((s) => !inPickers.has(s.vm))
    .find((s) => selectOptions(s).some((o) => o.label === option))
  if (!select) throw new Error(`no select offering "${option}"`)
  return select
}

const selectOptions = (select: VueWrapper) =>
  (select.props() as { options: { label: string; value: string }[] }).options

/** All options of the select that offers `option`, by their label. */
export const optionsBeside = (wrapper: VueWrapper, option: string) =>
  selectOptions(plainSelect(wrapper, option)).map((o) => o.label)

/** Chooses `option` in the select offering it. */
export async function selectOption(wrapper: VueWrapper, option: string) {
  const select = plainSelect(wrapper, option)
  const value = selectOptions(select).find((o) => o.label === option)!.value
  select.vm.$emit(
    'update:value',
    (select.props() as { multiple?: boolean }).multiple ? [value] : value,
  )
  await flushPromises()
}

/** Flips the switch of the toggle row with this label. */
export async function toggle(label: string) {
  const row = [...document.body.querySelectorAll('label.toggle')].find((el) =>
    el.querySelector('.label')?.textContent?.trim().startsWith(label),
  )
  if (!row) throw new Error(`no toggle "${label}"`)
  row.querySelector<HTMLElement>('.n-switch')!.click()
  await flushPromises()
}

export async function type(target: string | HTMLInputElement, value: string) {
  const input = typeof target === 'string' ? field(target) : target
  input.value = value
  input.dispatchEvent(new Event('input'))
  // Number fields with a precision take the value when the field is left.
  input.dispatchEvent(new FocusEvent('blur'))
  await flushPromises()
}

/** Clicks the radio button with this text. */
export async function choose(text: string) {
  const label = [...document.body.querySelectorAll('label.n-radio-button')]
    .filter((el) => el.textContent?.trim() === text)
    .at(-1)
  if (!label) throw new Error(`no radio button "${text}"`)
  label.querySelector('input')!.click()
  await flushPromises()
}

/**
 * Picks `id` in the `index`th searchable select loading from `fetcher`, as if the
 * user chose it from the list. The record must be among those the fetcher returned.
 */
export async function pick(wrapper: VueWrapper, fetcher: unknown, id: string | null, index = 0) {
  const select = wrapper
    .findAllComponents(EntitySelect)
    .filter((s) => (s.props() as { fetcher: unknown }).fetcher === fetcher)
    .at(index)
  if (!select) throw new Error('no such select')
  select.findComponent(NSelect).vm.$emit('update:value', id)
  await flushPromises()
}

// Small reference records, shared by the scenarios below.

export const userRef = (name = 'Jane Doe', id = 'u1'): Schemas['UserRefOut'] => ({
  id,
  username: name.toLowerCase().replace(' ', '.'),
  display_name: name,
})

export const modelRef = (
  name = 'Latitude 5450',
  tracking: Schemas['Tracking'] = 'serialized',
  id = 'm1',
): Schemas['AssetModelRefOut'] => ({
  id,
  name,
  designation: '',
  full_name: `Dell ${name}`,
  tracking,
})

export const categoryRef = (name = 'Laptops'): Schemas['CategoryRefOut'] => ({
  id: 'c1',
  code: 'NB',
  icon: 'laptop',
  item_name: 'Laptop',
  identifier_label: '',
  kind: 'hardware',
  name,
})

export const locationRef = (name = 'Main office'): Schemas['LocationRefOut'] => ({
  id: 'l1',
  name,
  full_name: `HQ / ${name}`,
})

/** A full model record as the model picker lists it. */
export function makeModel(overrides: Partial<Schemas['AssetModelOut']> = {}) {
  return {
    ...modelRef(),
    category: categoryRef(),
    compatible_with: [],
    default_supplier: null,
    predecessor: null,
    description: '',
    ean: '',
    effective_number_sequence: null,
    effective_team: null,
    is_active: true,
    is_requestable: true,
    list_price: null,
    manufacturer: { id: 'mf1', name: 'Dell' },
    number_sequence: null,
    part_number: '',
    specifications: '',
    team: null,
    warranty_months: 0,
    ...overrides,
  } satisfies Schemas['AssetModelOut']
}

/** A device in stock, as its detail page loads it. */
export function makeAsset(overrides: Partial<Schemas['AssetDetailOut']> = {}) {
  return {
    id: 'a1',
    reserved_for: null,
    inventory_number: 'NB-0042',
    serial_number: 'SN-1',
    identifier: '',
    imei: '',
    mac_address: '',
    hostname: 'nb-0042',
    status: 'in_stock',
    condition: 'good',
    is_loanable: true,
    model: modelRef(),
    category: categoryRef(),
    manufacturer: { id: 'mf1', name: 'Dell' },
    location: locationRef(),
    assigned_to: null,
    assigned_since: null,
    asset_request: null,
    parent: null,
    components: [],
    installed_components: [],
    supplier: null,
    purchase_date: '2025-03-01',
    purchase_price: '1299.00',
    warranty_until: '2028-03-01',
    consumables: [],
    model_consumables: [],
    licenses: [],
    open_issues: [],
    notes: '',
    created_at: '2025-03-01T09:00:00Z',
    updated_at: '2025-03-01T09:00:00Z',
    ...overrides,
  } satisfies Schemas['AssetDetailOut']
}

/** Icon buttons carry their meaning in the title. */
export const titled = (title: string, within: ParentNode = document.body) => [
  ...within.querySelectorAll<HTMLButtonElement>(`button[title="${title}"]`),
]

/** Picks a grouping from the grouping menu of a table toolbar. */
export async function groupBy(label: string) {
  const button = document.body.querySelectorAll<HTMLButtonElement>('.table-toolbar .toolbar button')
  const trigger = [...button].find((b) => b.querySelector('.lucide-group'))
  if (!trigger) throw new Error('no grouping menu')
  trigger.click()
  await flushPromises()
  const option = [...document.body.querySelectorAll<HTMLElement>('.n-base-select-option')].find(
    (el) => el.textContent?.trim() === label,
  )
  if (!option) throw new Error(`no grouping "${label}"`)
  option.click()
  await flushPromises()
}

/** Removes the active filter whose chip starts with this label. */
export async function clearChip(label: string) {
  const chip = [...document.body.querySelectorAll<HTMLElement>('.filter-chips .n-tag')].find(
    (el) => el.querySelector('.chip-label')?.textContent?.trim() === label,
  )
  if (!chip) throw new Error(`no filter chip "${label}"`)
  chip.querySelector<HTMLElement>('.n-tag__close, .n-base-close')!.click()
  await flushPromises()
}

/**
 * Adds a line to the filter panel of a table toolbar and picks the field `label` (as the
 * field menu shows it, e.g. "Purchase date (from)"). Opens the panel first if needed.
 */
export async function addFilter(wrapper: VueWrapper, label: string) {
  const panel = document.body.querySelector<HTMLElement>('.filter-panel')
  if (!panel || panel.style.display === 'none') {
    const toggle = [
      ...document.body.querySelectorAll<HTMLButtonElement>('.table-toolbar .toolbar button'),
    ].find((b) => b.querySelector('.lucide-list-filter'))
    if (!toggle) throw new Error('no filter button')
    toggle.click()
    await flushPromises()
  }
  const fields = () =>
    wrapper.findAllComponents(NSelect).filter((s) => s.element.closest?.('.rule-field'))
  let field = fields().find((s) => s.props('value') === null)
  if (!field) {
    document.body.querySelector<HTMLButtonElement>('.rule-add button')!.click()
    await flushPromises()
    field = fields().find((s) => s.props('value') === null)
  }
  const options = (field!.props('options') ?? []) as { value: string; label: string }[]
  const option = options.find((o) => o.label === label)
  if (!option) throw new Error(`no filter field "${label}" in ${options.map((o) => o.label)}`)
  field!.vm.$emit('update:value', option.value)
  await flushPromises()
}
