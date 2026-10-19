import { departmentsApi } from '@/api/accounts'
import { mono } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import type { Department } from '@/types/accounts'

export default defineResource<Department>({
  key: 'departments',
  api: departmentsApi,
  ordering: 'sort_order',
  title: (d) => d.name,
  columns: [
    { key: 'name', label: 'common.name', sorter: 'name' },
    { key: 'code', label: 'common.code', sorter: 'code', width: 140, render: (d) => mono(d.code) },
    {
      key: 'cost_center',
      label: 'masterdata.fields.costCenter',
      sorter: 'cost_center',
      width: 160,
      render: (d) => mono(d.cost_center),
    },
    {
      key: 'member_count',
      label: 'masterdata.fields.members',
      width: 110,
      render: (d) => mono(d.member_count),
    },
    {
      key: 'sort_order',
      label: 'masterdata.fields.sortOrder',
      sorter: 'sort_order',
      width: 110,
      render: (d) => mono(d.sort_order),
    },
  ],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true, span: 2 },
        { key: 'code', label: 'common.code', type: 'mono' },
        { key: 'cost_center', label: 'masterdata.fields.costCenter', type: 'mono' },
        {
          key: 'sort_order',
          label: 'masterdata.fields.sortOrder',
          type: 'number',
          min: 0,
          help: 'masterdata.fields.departmentSortHelp',
        },
      ],
    },
  ],
  defaults: () => ({ name: '', code: '', cost_center: '', sort_order: 0 }),
  toForm: (d) => ({
    name: d.name,
    code: d.code,
    cost_center: d.cost_center,
    sort_order: d.sort_order,
  }),
})
