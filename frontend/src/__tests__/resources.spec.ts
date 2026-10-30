import { createPinia, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it } from 'vitest'

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
