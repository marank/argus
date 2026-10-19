import { categoriesApi, numberSequencesApi } from '@/api/masterdata'
import { bool, mono, withIcon } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import type { Category } from '@/types/masterdata'

export default defineResource<Category>({
  key: 'categories',
  api: categoriesApi,
  ordering: 'sort_order',
  title: (c) => c.name,
  columns: [
    {
      key: 'name',
      label: 'common.name',
      sorter: 'name',
      render: (c) => withIcon(c.icon, c.path.join(' / ')),
    },
    { key: 'code', label: 'common.code', sorter: 'code', width: 160, render: (c) => mono(c.code) },
    {
      key: 'number_sequence',
      label: 'masterdata.fields.numberSequence',
      width: 200,
      render: (c) => c.number_sequence?.name ?? '—',
    },
    {
      key: 'is_requestable',
      label: 'masterdata.fields.requestable',
      width: 150,
      render: (c) => bool(c.is_requestable),
    },
    {
      key: 'sort_order',
      label: 'masterdata.fields.sortOrder',
      sorter: 'sort_order',
      width: 110,
      render: (c) => mono(c.sort_order),
    },
  ],
  filters: [{ key: 'is_requestable', label: 'masterdata.fields.requestable', type: 'boolean' }],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true },
        { key: 'code', label: 'common.code', type: 'mono', required: true },
        {
          key: 'parent',
          label: 'masterdata.fields.parent',
          type: 'entity',
          fetcher: categoriesApi.list,
          display: (c: Category) => c.path.join(' / '),
          initial: (c: Category) => c.parent,
        },
        { key: 'icon', label: 'masterdata.fields.icon', type: 'icon' },
        { key: 'description', label: 'common.description', type: 'textarea' },
      ],
    },
    {
      title: 'masterdata.sections.numbering',
      fields: [
        {
          key: 'number_sequence',
          label: 'masterdata.fields.numberSequence',
          type: 'entity',
          span: 2,
          help: 'masterdata.fields.numberSequenceHelp',
          fetcher: numberSequencesApi.list,
          display: (s: { name: string; preview?: string }) =>
            s.preview ? `${s.name} · ${s.preview}` : s.name,
          initial: (c: Category) => c.number_sequence,
        },
      ],
    },
    {
      title: 'masterdata.sections.portal',
      fields: [
        { key: 'is_requestable', label: 'masterdata.fields.requestable', type: 'switch' },
        {
          key: 'allow_any_model',
          label: 'masterdata.fields.allowAnyModel',
          type: 'switch',
          help: 'masterdata.fields.allowAnyModelHelp',
        },
        { key: 'sort_order', label: 'masterdata.fields.sortOrder', type: 'number', min: 0 },
      ],
    },
  ],
  defaults: () => ({
    name: '',
    code: '',
    parent: null,
    description: '',
    icon: '',
    number_sequence: null,
    is_requestable: true,
    allow_any_model: true,
    sort_order: 0,
  }),
  toForm: (c) => ({
    name: c.name,
    code: c.code,
    parent: c.parent?.id ?? null,
    description: c.description,
    icon: c.icon,
    number_sequence: c.number_sequence?.id ?? null,
    is_requestable: c.is_requestable,
    allow_any_model: c.allow_any_model,
    sort_order: c.sort_order,
  }),
})
