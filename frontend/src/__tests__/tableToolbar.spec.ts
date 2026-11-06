import { flushPromises, mount, type VueWrapper } from '@vue/test-utils'
import { NPopover, NPopselect, NRadioGroup, NSelect } from 'naive-ui'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { defineComponent, h, reactive, ref } from 'vue'

import EntitySelect from '@/components/common/EntitySelect.vue'
import ColumnSettings from '@/components/table/ColumnSettings.vue'
import DateRangeInput from '@/components/table/DateRangeInput.vue'
import TableToolbar from '@/components/table/TableToolbar.vue'
import type { TableColumn, TableFilter } from '@/components/table/types'
import { useTableView } from '@/composables/useTableView'
import { i18n } from '@/i18n'

interface Row {
  id: string
  kind: string
}

const FILTERS: TableFilter[] = [
  {
    key: 'status',
    label: 'Status',
    type: 'select',
    options: [
      { value: 'open', label: 'Open' },
      { value: 'done', label: 'Done' },
    ],
  },
  { key: 'active', label: 'Active', type: 'boolean' },
  { key: 'mine', label: 'Mine only', type: 'toggle', on: () => true },
  { key: 'due', label: 'Due', type: 'daterange', from: 'due_from', until: 'due_until' },
  {
    key: 'team',
    label: 'Team',
    type: 'entity',
    fetcher: async () => ({ items: [{ id: 't1', name: 'Service desk' }], count: 1 }),
    display: (team: { name: string }) => team.name,
  },
]

const COLUMNS: TableColumn<Row>[] = [
  { key: 'name', title: 'Name', hideable: false },
  { key: 'kind', title: 'Kind', width: 100 },
  { key: 'notes', title: 'Notes', width: 100 },
  { key: 'zeta', title: 'Zeta', width: 100, hidden: true },
  { key: 'alpha', title: 'Alpha', width: 100, hidden: true },
]

let wrapper: VueWrapper | null = null

function mountToolbar(values: Record<string, unknown> = {}) {
  const filters = reactive<Record<string, unknown>>({
    status: [],
    active: null,
    mine: null,
    team: null,
    due_from: null,
    due_until: null,
    ...values,
  })
  const list = { filters, setFilter: (key: string, value: unknown) => (filters[key] = value) }
  const search = ref('')
  let view!: ReturnType<typeof useTableView<Row>>
  wrapper = mount(
    defineComponent({
      setup() {
        view = useTableView<Row>({
          id: 'toolbar',
          columns: () => COLUMNS,
          rows: () => [],
          groupings: () => [
            {
              key: 'kind',
              label: 'Kind',
              ordering: 'kind',
              rowKey: (r) => r.kind,
              rowLabel: (r) => r.kind,
            },
          ],
        })
        return () =>
          h(TableToolbar, {
            list,
            filters: FILTERS,
            view,
            search: search.value,
            'onUpdate:search': (value: string) => (search.value = value),
          })
      },
    }),
    { attachTo: document.body, global: { plugins: [i18n] } },
  )
  return { filters, view, search }
}

const chips = () =>
  [...document.body.querySelectorAll('.filter-chips .n-tag')].map((el) =>
    el.textContent?.replace(/\s+/g, ' ').trim(),
  )

describe('TableToolbar', () => {
  beforeEach(() => localStorage.clear())
  afterEach(() => {
    wrapper?.unmount()
    wrapper = null
  })

  /** The select of a filter line: its field, or its value for the line of `key`. */
  const fieldSelect = (key: string | null) =>
    wrapper!
      .findAllComponents(NSelect)
      .find(
        (s) =>
          s.element.closest?.('.rule-field') &&
          (s.element.closest('.rule')?.getAttribute('data-filter') ?? null) === key,
      )!
  const valueSelect = (key: string) =>
    wrapper!
      .findAllComponents(NSelect)
      .find(
        (s) =>
          s.element.closest?.('.rule-value') &&
          s.element.closest('.rule')?.getAttribute('data-filter') === key,
      )!
  /** Each line as "field operator"; the field by its key, "?" while not chosen. */
  const lines = () =>
    [...document.body.querySelectorAll('.filter-panel .rule')].map((el) =>
      [el.getAttribute('data-filter') ?? '?', el.querySelector('.rule-op')!.textContent].join(' '),
    )
  const toggle = () => wrapper!.find('.toolbar button').trigger('click')
  const panel = () => document.body.querySelector<HTMLElement>('.filter-panel')!

  it('shows a line and a chip per active filter', async () => {
    const { filters } = mountToolbar({
      status: ['open', 'done'],
      active: 'false',
      mine: true,
      due_from: '2026-12-01',
    })
    await flushPromises()
    expect(chips().slice(0, 3)).toEqual(['Status: Open, Done', 'Active: No', 'Mine only'])
    expect(chips()[3]).toBe('Due: 01.12.26..')
    expect(panel().style.display).toBe('none')

    await toggle()
    expect(panel().style.display).toBe('')
    expect(lines()).toEqual(['status is', 'active is', 'mine is', 'due is'])
    expect(document.body.querySelectorAll('.rule.set')).toHaveLength(4)
    // The open panel shows the filters itself.
    expect(chips()).toEqual([])

    valueSelect('status').vm.$emit('update:value', ['done'])
    valueSelect('active').vm.$emit('update:value', 'true')
    await flushPromises()
    expect(filters.status).toEqual(['done'])
    await toggle()
    expect(chips()).toContain('Active: Yes')
  })

  it('adds, changes and removes filter lines', async () => {
    const { filters } = mountToolbar()
    await toggle()
    // An empty panel starts with a line to fill in.
    expect(lines()).toEqual(['? is'])
    const fields = fieldSelect(null).props('options') as { value: string; label: string }[]
    // Alphabetically, whatever the order of the table's filters.
    expect(fields.map((o) => o.label)).toEqual(['Active', 'Due', 'Mine only', 'Status', 'Team'])

    fieldSelect(null).vm.$emit('update:value', 'team')
    await flushPromises()
    wrapper!.findComponent(EntitySelect).vm.$emit('update:modelValue', 't1')
    await flushPromises()
    expect(filters.team).toBe('t1')
    expect(document.body.querySelector('.rule[data-filter="team"]')!.classList).toContain('set')

    document.body.querySelector<HTMLButtonElement>('.rule-add button')!.click()
    await flushPromises()
    const left = fieldSelect(null).props('options') as { value: string }[]
    expect(left.map((o) => o.value)).not.toContain('team')
    fieldSelect(null).vm.$emit('update:value', 'mine')
    await flushPromises()
    expect(filters.mine).toBe(true)

    // Another field on the same line drops the old filter.
    fieldSelect('team').vm.$emit('update:value', 'due')
    await flushPromises()
    expect(filters.team).toBeNull()
    const range = wrapper!.findComponent(DateRangeInput).find('input')
    await range.setValue('2412..3112')
    await range.trigger('blur')
    expect(filters).toMatchObject({ due_from: '2026-12-24', due_until: '2026-12-31' })
    expect(range.element.value).toBe('24.12.26..31.12.26')
    await range.setValue('3112..2412')
    await range.trigger('keydown', { key: 'Enter' })
    // Text that cannot be read stays as typed and changes nothing.
    expect(range.element.value).toBe('3112..2412')
    expect(filters.due_until).toBe('2026-12-31')

    document.body
      .querySelector<HTMLButtonElement>('.rule[data-filter="mine"] .rule-remove')!
      .click()
    await flushPromises()
    expect(filters.mine).toBeNull()
    expect(lines()).toEqual(['due is'])

    document.body.querySelector<HTMLElement>('.panel-head .clear-all')!.click()
    await flushPromises()
    expect(filters).toMatchObject({
      status: [],
      active: null,
      mine: null,
      team: null,
      due_from: null,
      due_until: null,
    })
    expect(lines()).toEqual([])
    expect(chips()).toEqual([])
  })

  it('removes the line of a filter cleared by its chip', async () => {
    const { filters } = mountToolbar({ status: ['open'] })
    await flushPromises()
    document.body
      .querySelector<HTMLElement>(
        '.filter-chips .n-tag .n-base-close, .filter-chips .n-tag__close',
      )!
      .click()
    await flushPromises()
    expect(filters.status).toEqual([])
    await toggle()
    expect(lines()).toEqual(['? is'])
  })

  it('picks a grouping and none again', async () => {
    const { view } = mountToolbar()
    const menu = wrapper!.findComponent(NPopselect)
    menu.vm.$emit('update:value', 'kind')
    await flushPromises()
    expect(view.groupOrdering()).toBe('kind')
    menu.vm.$emit('update:value', '__none')
    await flushPromises()
    expect(view.groupOrdering()).toBeUndefined()
  })

  it('shows, hides and reorders columns in the column settings', async () => {
    const { view } = mountToolbar()
    const settings = wrapper!.findComponent(ColumnSettings)
    settings.findComponent(NPopover).vm.$emit('update:show', true)
    await settings.find('button').trigger('click')
    await flushPromises()

    const items = () => [...document.body.querySelectorAll<HTMLElement>('.column-list li')]
    const titles = () => items().map((li) => li.textContent?.trim())
    const tick = async (title: string) => {
      items()
        .find((li) => li.textContent?.trim() === title)!
        .querySelector<HTMLElement>('.n-checkbox')!
        .click()
      await flushPromises()
    }
    // The shown columns in their order, then the hidden ones alphabetically.
    expect(titles()).toEqual(['Name', 'Kind', 'Notes', 'Alpha', 'Zeta'])
    expect(items()[0]!.getAttribute('draggable')).toBe('false')

    // Switched on or off, a column keeps its place while the list is open.
    await tick('Kind')
    await tick('Alpha')
    expect(view.settingColumns.value.find((c) => c.key === 'kind')!.visible).toBe(false)
    expect(titles()).toEqual(['Name', 'Kind', 'Notes', 'Alpha', 'Zeta'])
    expect(view.settingColumns.value.filter((c) => c.visible).map((c) => c.key)).toEqual([
      'name',
      'notes',
      'alpha',
    ])
    // Opened again, it sorts anew.
    settings.findComponent(NPopover).vm.$emit('update:show', true)
    await flushPromises()
    expect(titles()).toEqual(['Name', 'Notes', 'Alpha', 'Kind', 'Zeta'])

    const drag = (type: string) => new Event(type, { bubbles: true, cancelable: true })
    items()[2]!.dispatchEvent(drag('dragstart'))
    items()[1]!.dispatchEvent(drag('dragover'))
    items()[1]!.dispatchEvent(drag('dragleave'))
    items()[1]!.dispatchEvent(drag('dragover'))
    items()[1]!.dispatchEvent(drag('drop'))
    await flushPromises()
    expect(titles()).toEqual(['Name', 'Alpha', 'Notes', 'Kind', 'Zeta'])
    expect(view.settingColumns.value.map((c) => c.key)).toEqual([
      'name',
      'alpha',
      'notes',
      'kind',
      'zeta',
    ])

    wrapper!.findComponent(NRadioGroup).vm.$emit('update:value', 'medium')
    expect(view.density.value).toBe('medium')
    const reset = [...document.body.querySelectorAll<HTMLButtonElement>('.column-settings button')]
    reset.at(-1)!.click()
    await flushPromises()
    expect(view.customized.value).toBe(false)
  })
})
