import { manufacturersApi } from '@/api/masterdata'
import { bool, text } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import type { Manufacturer } from '@/types/masterdata'

export default defineResource<Manufacturer>({
  key: 'manufacturers',
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
