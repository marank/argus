import { suppliersApi } from '@/api/masterdata'
import { bool, mono, text } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import type { Supplier } from '@/types/masterdata'

export default defineResource<Supplier>({
  key: 'suppliers',
  api: suppliersApi,
  ordering: 'name',
  title: (s) => s.name,
  columns: [
    { key: 'name', label: 'common.name', sorter: 'name' },
    {
      key: 'customer_number',
      label: 'masterdata.fields.customerNumber',
      sorter: 'customer_number',
      width: 150,
      render: (s) => mono(s.customer_number),
    },
    {
      key: 'contact_person',
      label: 'masterdata.fields.contactPerson',
      sorter: 'contact_person',
      render: (s) => text(s.contact_person),
    },
    { key: 'email', label: 'masterdata.fields.email', render: (s) => text(s.email) },
    { key: 'phone', label: 'masterdata.fields.phone', width: 160, render: (s) => text(s.phone) },
    { key: 'is_active', label: 'common.active', width: 90, render: (s) => bool(s.is_active) },
  ],
  filters: [{ key: 'is_active', label: 'common.active', type: 'boolean' }],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true, span: 2 },
        { key: 'customer_number', label: 'masterdata.fields.customerNumber', type: 'mono' },
        { key: 'is_active', label: 'common.active', type: 'switch' },
      ],
    },
    {
      title: 'masterdata.sections.contact',
      fields: [
        { key: 'contact_person', label: 'masterdata.fields.contactPerson', type: 'text' },
        { key: 'phone', label: 'masterdata.fields.phone', type: 'text' },
        { key: 'email', label: 'masterdata.fields.email', type: 'text' },
        { key: 'website', label: 'masterdata.fields.website', type: 'text' },
        { key: 'address', label: 'masterdata.fields.address', type: 'textarea' },
      ],
    },
    {
      title: 'masterdata.sections.notes',
      fields: [{ key: 'notes', label: 'common.notes', type: 'textarea' }],
    },
  ],
  defaults: () => ({
    name: '',
    customer_number: '',
    contact_person: '',
    email: '',
    phone: '',
    website: '',
    address: '',
    notes: '',
    is_active: true,
  }),
  toForm: ({ id: _id, ...rest }) => rest,
})
