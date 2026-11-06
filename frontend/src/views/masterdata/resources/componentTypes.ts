import { categoriesApi, componentTypesApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import { mono } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'

/** Replaceable parts tracked on devices, e.g. the battery, and the categories that have them. */
export default defineResource<Schemas['ComponentTypeOut']>({
  key: 'componentTypes',
  // Part of setting up the categories.
  permission: 'categories',
  api: componentTypesApi,
  ordering: 'sort_order',
  title: (c) => c.name,
  columns: [
    { key: 'name', label: 'common.name', sorter: 'name' },
    {
      key: 'categories',
      label: 'masterdata.resources.categories',
      render: (c) => c.categories.map((category) => category.name).join(', ') || '—',
    },
    {
      key: 'sort_order',
      label: 'masterdata.fields.sortOrder',
      sorter: 'sort_order',
      width: 110,
      render: (c) => mono(c.sort_order),
    },
  ],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true },
        { key: 'sort_order', label: 'masterdata.fields.sortOrder', type: 'number', min: 0 },
        {
          key: 'categories',
          label: 'masterdata.resources.categories',
          type: 'entity',
          multiple: true,
          help: 'masterdata.fields.componentCategoriesHelp',
          fetcher: categoriesApi.list,
          display: (c: { name: string; path?: string[] }) => c.path?.join(' / ') ?? c.name,
          initial: (c: Schemas['ComponentTypeOut']) => c.categories,
        },
      ],
    },
  ],
  defaults: () => ({ name: '', categories: [], sort_order: 0 }),
  toForm: (c) => ({
    name: c.name,
    categories: c.categories.map((category) => category.id),
    sort_order: c.sort_order,
  }),
})
