import { Building2 } from '@lucide/vue'
import { h } from 'vue'

import { departmentsApi, usersApi } from '@/api/accounts'
import { bool, mono, text } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'
import type { User } from '@/types/accounts'

export default defineResource<User>({
  key: 'users',
  // Sections per department.
  groupBy: {
    ordering: 'department__sort_order,department__name',
    key: (u) => u.department?.id ?? 'none',
    label: (u) => [
      h(Building2, { size: 14 }),
      u.department?.name ?? i18n.global.t('masterdata.noDepartment'),
    ],
  },
  api: usersApi,
  ordering: 'last_name',
  title: (u) => u.display_name,
  columns: [
    { key: 'display_name', label: 'common.name', sorter: 'last_name' },
    {
      key: 'username',
      label: 'masterdata.fields.username',
      sorter: 'username',
      width: 150,
      render: (u) => mono(u.username),
    },
    {
      key: 'employee_number',
      label: 'masterdata.fields.employeeNumber',
      sorter: 'employee_number',
      width: 140,
      render: (u) => mono(u.employee_number),
    },
    {
      key: 'department',
      label: 'masterdata.fields.department',
      width: 160,
      render: (u) => u.department?.name ?? '—',
    },
    {
      key: 'email',
      label: 'masterdata.fields.email',
      sorter: 'email',
      render: (u) => text(u.email),
    },
    {
      key: 'is_it_staff',
      label: 'masterdata.fields.itStaff',
      width: 100,
      render: (u) => bool(u.is_it_staff),
    },
    {
      key: 'is_terminal',
      label: 'masterdata.fields.terminal',
      width: 100,
      render: (u) => bool(u.is_terminal),
    },
    {
      key: 'is_ldap_user',
      label: 'masterdata.fields.ldap',
      width: 80,
      render: (u) => bool(u.is_ldap_user),
    },
    { key: 'is_active', label: 'common.active', width: 80, render: (u) => bool(u.is_active) },
  ],
  filters: [
    {
      key: 'department',
      label: 'masterdata.fields.department',
      type: 'entity',
      fetcher: departmentsApi.list,
      display: (d: { name: string }) => d.name,
    },
    { key: 'is_staff', label: 'masterdata.fields.itStaff', type: 'boolean' },
    { key: 'is_active', label: 'common.active', type: 'boolean' },
  ],
  sections: [
    {
      title: 'masterdata.sections.person',
      fields: [
        { key: 'first_name', label: 'masterdata.fields.firstName', type: 'text' },
        { key: 'last_name', label: 'masterdata.fields.lastName', type: 'text' },
        { key: 'email', label: 'masterdata.fields.email', type: 'text' },
        { key: 'phone', label: 'masterdata.fields.phone', type: 'text' },
      ],
    },
    {
      title: 'masterdata.sections.organisation',
      fields: [
        {
          key: 'department',
          label: 'masterdata.fields.department',
          type: 'entity',
          fetcher: departmentsApi.list,
          display: (d: { name: string }) => d.name,
          initial: (u: User) => u.department,
        },
        { key: 'job_title', label: 'masterdata.fields.jobTitle', type: 'text' },
        { key: 'employee_number', label: 'masterdata.fields.employeeNumber', type: 'mono' },
      ],
    },
    {
      title: 'masterdata.sections.account',
      fields: [
        { key: 'username', label: 'masterdata.fields.username', type: 'mono', required: true },
        { key: 'is_active', label: 'common.active', type: 'switch' },
        {
          key: 'is_staff',
          label: 'masterdata.fields.itStaff',
          type: 'switch',
          help: 'masterdata.fields.itStaffHelp',
        },
        {
          key: 'is_terminal',
          label: 'masterdata.fields.terminal',
          type: 'switch',
          help: 'masterdata.fields.terminalHelp',
        },
      ],
    },
  ],
  defaults: () => ({
    username: '',
    first_name: '',
    last_name: '',
    email: '',
    employee_number: '',
    job_title: '',
    phone: '',
    department: null,
    is_staff: false,
    is_terminal: false,
    is_active: true,
  }),
  toForm: (u) => ({
    username: u.username,
    first_name: u.first_name,
    last_name: u.last_name,
    email: u.email,
    employee_number: u.employee_number,
    job_title: u.job_title,
    phone: u.phone,
    department: u.department?.id ?? null,
    is_staff: u.is_it_staff,
    is_terminal: u.is_terminal,
    is_active: u.is_active,
  }),
})
