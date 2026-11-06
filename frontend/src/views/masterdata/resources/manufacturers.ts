import type { Schemas } from '@/api/types'
import { manufacturersApi } from '@/api/masterdata'
import { bool, text } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'

export default defineResource<Schemas['ManufacturerOut']>({
  key: 'manufacturers',
  permission: 'manufacturers',
  api: manufacturersApi,
  ordering: 'name',
  title: (m) => m.name,
  columns: [
    { key: 'name', label: 'common.name', sorter: 'name' },
    { key: 'website', label: 'masterdata.fields.website', render: (m) => text(m.website) },
    {
      key: 'support_phone',
      label: 'masterdata.fields.supportPhone',
      width: 180,
      render: (m) => text(m.support_phone),
    },
    { key: 'is_active', label: 'common.active', width: 90, render: (m) => bool(m.is_active) },
    // Further columns to show from the column settings.
    {
      key: 'support_url',
      label: 'masterdata.fields.supportUrl',
      hidden: true,
      width: 200,
      render: (m) => text(m.support_url),
    },
    { key: 'notes', label: 'common.notes', hidden: true, render: (m) => text(m.notes) },
  ],
  filters: [{ key: 'is_active', label: 'common.active', type: 'boolean' }],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true },
        { key: 'is_active', label: 'common.active', type: 'switch' },
      ],
    },
    {
      title: 'masterdata.sections.support',
      fields: [
        { key: 'website', label: 'masterdata.fields.website', type: 'text' },
        { key: 'support_url', label: 'masterdata.fields.supportUrl', type: 'text' },
        { key: 'support_phone', label: 'masterdata.fields.supportPhone', type: 'text' },
      ],
    },
    {
      title: 'masterdata.sections.notes',
      fields: [{ key: 'notes', label: 'common.notes', type: 'textarea' }],
    },
  ],
  defaults: () => ({
    name: '',
    website: '',
    support_url: '',
    support_phone: '',
    notes: '',
    is_active: true,
  }),
  toForm: ({ id: _id, ...rest }) => rest,
})
