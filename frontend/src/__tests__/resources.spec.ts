import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

import type { Schemas } from '@/api/types'
import { sectionFields } from '@/components/crud/types'
import { i18n } from '@/i18n'
import { RESOURCES } from '@/views/masterdata/resources'

const resources = Object.values(RESOURCES)
const exists = (key: string) => i18n.global.te(key, 'en') && i18n.global.te(key, 'de')

describe.each(resources.map((resource) => [resource.key, resource] as const))(
  'master data resource %s',
  (key, resource) => {
    beforeEach(() => setActivePinia(createPinia()))

    it('is registered under its own key', () => {
      expect(RESOURCES[key]).toBe(resource)
    })

    it('has a title and singular in both languages', () => {
      expect(exists(`masterdata.resources.${key}`)).toBe(true)
      expect(exists(`masterdata.singular.${key}`)).toBe(true)
    })

    it('starts a new record with a value for every field', () => {
      const defaults = resource.defaults()
      const missing = sectionFields(resource)
        .map((field) => field.key)
        .filter((field) => !(field in defaults))
      expect(missing).toEqual([])
    })

    it('labels fields, sections, columns and filters in both languages', () => {
      const keys = [
        ...sectionFields(resource).map((field) => field.label),
        ...resource.sections.flatMap((section) => (section.title ? [section.title] : [])),
        ...resource.columns.map((column) => column.label),
        ...(resource.filters ?? []).map((filter) => filter.label),
      ]
      expect(keys.filter((label) => !exists(label))).toEqual([])
    })

    it('names the field explanations in both languages', () => {
      const help = sectionFields(resource)
        .map((field) => (typeof field.help === 'function' ? field.help() : field.help))
        .filter((help): help is string => !!help)
      expect(help.filter((help) => !exists(help))).toEqual([])
    })

    it('translates the values of enum fields', () => {
      const missing = sectionFields(resource).flatMap((field) =>
        field.type === 'enum'
          ? field.values.map((value) => `enums.${field.group}.${value}`).filter((k) => !exists(k))
          : [],
      )
      expect(missing).toEqual([])
    })

    it('has unique field and column keys', () => {
      const fields = sectionFields(resource).map((field) => field.key)
      expect(new Set(fields).size).toBe(fields.length)
      const columns = resource.columns.map((column) => column.key)
      expect(new Set(columns).size).toBe(columns.length)
    })
  },
)

describe('categories resource', () => {
  const categories = RESOURCES.categories!
  const category = (overrides: Partial<Schemas['CategoryOut']> = {}): Schemas['CategoryOut'] => ({
    id: 'c1',
    name: 'MDEs',
    kind: 'hardware',
    item_name: 'MDE',
    code: 'mde',
    identifier_label: 'CN',
    parent: null,
    description: '',
    icon: 'barcode',
    number_sequence: { id: 's1', name: 'MDE numbers' },
    device_naming: 'none',
    name_sequence: null,
    is_requestable: true,
    model_choice: 'any_only',
    requires_approval: false,
    is_accessory: false,
    needs_approval: false,
    holds_accessories: false,
    sort_order: 0,
    path: ['MDEs'],
    team: null,
    effective_team: null,
    ...overrides,
  })
  const rows = [
    category(),
    category({
      kind: 'software',
      code: '',
      item_name: '',
      identifier_label: '',
      number_sequence: null,
      parent: { id: 'c0', name: 'Software' },
      path: ['Software', 'Office'],
      needs_approval: true,
      team: { id: 't1', name: 'Workplace' } as never,
      effective_team: { id: 't1', name: 'Workplace' } as never,
    }),
    category({ requires_approval: true, needs_approval: true, device_naming: 'inventory_number' }),
    category({ device_naming: 'sequence', name_sequence: { id: 's2', name: 'H names' } }),
  ]
  const render = (key: string, row: Schemas['CategoryOut']) =>
    categories.columns.find((c) => c.key === key)!.render!(row)

  it('renders every column, grouping and tree label of a category', () => {
    for (const row of rows) {
      for (const column of categories.columns) column.render?.(row)
      for (const grouping of categories.groupings ?? []) {
        expect(grouping.rowKey(row)).toBe(row.kind)
        grouping.rowLabel(row)
      }
      categories.tree!.label(row)
      expect(categories.tree!.parent(row)).toBe(row.parent?.id)
      expect(categories.title?.(row)).toBe(row.name)
    }
  })

  it('shows where device names come from, the sequence by its name', () => {
    expect(render('device_naming', rows[0]!)).toBe('No name')
    expect(render('device_naming', rows[2]!)).toBe('Same as the inventory number')
    expect(render('device_naming', rows[3]!)).toBe('H names')
    expect(render('item_name', rows[1]!)).toBe('—')
    expect(render('number_sequence', rows[1]!)).toBe('—')
  })

  it('fills the form from a category and back', () => {
    expect(categories.toForm(rows[3]!)).toMatchObject({
      device_naming: 'sequence',
      name_sequence: 's2',
      number_sequence: 's1',
      parent: null,
    })
    expect(categories.toForm(rows[1]!)).toMatchObject({ parent: 'c0', team: 't1' })
    for (const field of sectionFields(categories)) {
      if (field.type !== 'entity') continue
      field.initial?.(rows[3]!)
      field.display({ name: 'Item', path: ['A', 'Item'], preview: 'H001' })
      field.display({ name: 'Item' })
    }
  })

  it('asks for the sequence only when device names come from one', () => {
    const field = sectionFields(categories).find((f) => f.key === 'name_sequence')!
    expect(field.visible!({ device_naming: 'sequence' })).toBe(true)
    expect(field.visible!({ device_naming: 'inventory_number' })).toBe(false)
  })
})
