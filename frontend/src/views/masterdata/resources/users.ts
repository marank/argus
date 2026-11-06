import type { Schemas } from '@/api/types'
import { Building2 } from '@lucide/vue'
import { NTag } from 'naive-ui'
import { h } from 'vue'

import { departmentsApi, rolesApi, teamsApi, usersApi } from '@/api/accounts'
import { locationsApi } from '@/api/masterdata'
import { bool, mono, text } from '@/components/crud/cells'
import TwoFactorReset from '@/components/masterdata/TwoFactorReset.vue'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'

/** Administrator, IT staff, terminal, LDAP and 2FA as small tags in one column. */
function accountFlags(u: Schemas['UserOut']) {
  const t = i18n.global.t
  const flags = [
    u.is_superuser && t('masterdata.fields.administratorShort'),
    u.is_it_staff && !u.is_superuser && t('masterdata.fields.itStaffShort'),
    u.is_terminal && t('masterdata.fields.terminalShort'),
    u.is_ldap_user && t('masterdata.fields.ldap'),
    u.two_factor && t('masterdata.twoFactor.column'),
  ].filter((flag): flag is string => !!flag)
  if (!flags.length) return h('span', { class: 'muted' }, '—')
  return h(
    'span',
    { class: 'row', style: 'gap:4px;flex-wrap:wrap' },
    flags.map((flag) => h(NTag, { size: 'small', bordered: false }, () => flag)),
  )
}

export default defineResource<Schemas['UserOut']>({
  key: 'users',
  permission: 'users',
  // Sections per department.
  groupings: [
    {
      key: 'department',
      label: 'masterdata.fields.department',
      ordering: 'department__sort_order,department__name',
      rowKey: (u) => u.department?.id ?? 'none',
      rowLabel: (u) => [
        h(Building2, { size: 14 }),
        u.department?.name ?? i18n.global.t('masterdata.noDepartment'),
      ],
    },
  ],
  api: usersApi,
  ordering: 'last_name',
  title: (u) => u.display_name,
  columns: [
    {
      key: 'display_name',
      label: 'common.name',
      sorter: 'last_name',
      render: (u) =>
        h('div', [
          u.display_name,
          h('small', { class: 'mono muted', style: 'display:block' }, u.username),
        ]),
    },
    {
      key: 'employee_number',
      label: 'masterdata.fields.employeeNumber',
      sorter: 'employee_number',
      width: 140,
      render: (u) => mono(u.employee_number),
    },
    {
      key: 'email',
      label: 'masterdata.fields.email',
      sorter: 'email',
      render: (u) => text(u.email),
    },
    {
      key: 'account',
      label: 'masterdata.fields.accountFlags',
      width: 150,
      render: (u) => accountFlags(u),
    },
    {
      key: 'roles',
      label: 'masterdata.resources.roles',
      width: 160,
      render: (u) => text(u.roles.map((r) => r.name).join(', ')),
      visible: () => useAuthStore().isItStaff,
    },
    { key: 'is_active', label: 'common.active', width: 80, render: (u) => bool(u.is_active) },
    // Further columns to show from the column settings.
    {
      key: 'username',
      label: 'masterdata.fields.username',
      hidden: true,
      width: 150,
      render: (u) => mono(u.username),
    },
    {
      key: 'first_name',
      label: 'masterdata.fields.firstName',
      hidden: true,
      width: 140,
      render: (u) => text(u.first_name),
    },
    {
      key: 'last_name',
      label: 'masterdata.fields.lastName',
      hidden: true,
      width: 140,
      render: (u) => text(u.last_name),
    },
    {
      key: 'phone',
      label: 'masterdata.fields.phone',
      hidden: true,
      width: 150,
      render: (u) => text(u.phone),
    },
    {
      key: 'job_title',
      label: 'masterdata.fields.jobTitle',
      hidden: true,
      width: 180,
      render: (u) => text(u.job_title),
    },
    {
      key: 'teams',
      label: 'masterdata.resources.teams',
      hidden: true,
      width: 180,
      render: (u) => text(u.teams.map((team) => team.name).join(', ')),
    },
  ],
  filters: [
    {
      key: 'department',
      label: 'masterdata.fields.department',
      type: 'entity',
      fetcher: departmentsApi.list,
      display: (d: { name: string; path?: string[] }) => d.path?.join(' / ') ?? d.name,
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
          display: (d: { name: string; path?: string[] }) => d.path?.join(' / ') ?? d.name,
          initial: (u: Schemas['UserOut']) => u.department,
        },
        { key: 'job_title', label: 'masterdata.fields.jobTitle', type: 'text' },
        { key: 'employee_number', label: 'masterdata.fields.employeeNumber', type: 'mono' },
        {
          key: 'approval_exempt',
          label: 'masterdata.fields.approvalExempt',
          type: 'switch',
          help: 'masterdata.fields.approvalExemptHelp',
        },
      ],
    },
    {
      title: 'masterdata.sections.account',
      fields: [
        {
          key: 'username',
          label: 'masterdata.fields.username',
          type: 'mono',
          required: true,
          help: () =>
            useFeaturesStore().ldapEnabled ? 'masterdata.fields.usernameLdapHelp' : undefined,
        },
        { key: 'is_active', label: 'common.active', type: 'switch' },
      ],
      extra: TwoFactorReset,
    },
    {
      title: 'masterdata.sections.permissions',
      // Teams and roles only apply to IT staff, so they appear below that switch.
      togglesFirst: true,
      fields: [
        {
          key: 'teams',
          label: 'masterdata.resources.teams',
          type: 'entity',
          multiple: true,
          span: 1,
          fetcher: teamsApi.list,
          display: (t: Schemas['RefOut']) => t.name,
          initial: (u: Schemas['UserOut']) => u.teams,
          help: () =>
            useFeaturesStore().ldapEnabled ? 'masterdata.fields.userTeamsLdapHelp' : undefined,
          visible: (form) => !!form.is_staff && useAuthStore().can('teams', 'write'),
        },
        {
          key: 'roles',
          label: 'masterdata.resources.roles',
          type: 'entity',
          multiple: true,
          span: 1,
          fetcher: rolesApi.list,
          display: (r: Schemas['RefOut']) => r.name,
          initial: (u: Schemas['UserOut']) => u.roles,
          help: 'masterdata.fields.userRolesHelp',
          // Administrators have every right anyway.
          visible: (form) => !!form.is_staff && !form.is_superuser && useAuthStore().isSuperuser,
        },
        {
          key: 'is_superuser',
          label: 'masterdata.fields.administrator',
          type: 'switch',
          help: 'masterdata.fields.administratorHelp',
          visible: () => useAuthStore().isSuperuser,
        },
        {
          key: 'is_staff',
          label: 'masterdata.fields.itStaff',
          type: 'switch',
          help: 'masterdata.fields.itStaffHelp',
        },
      ],
    },
    {
      title: 'masterdata.sections.terminal',
      togglesFirst: true,
      fields: [
        {
          key: 'is_terminal',
          label: 'masterdata.fields.terminal',
          type: 'switch',
          help: 'masterdata.fields.terminalHelp',
        },
        {
          key: 'terminal_location',
          label: 'masterdata.fields.terminalLocation',
          type: 'entity',
          span: 2,
          fetcher: locationsApi.list,
          display: (l: Schemas['LocationOut']) => l.full_name,
          initial: (u: Schemas['UserOut']) => u.terminal_location,
          help: 'masterdata.fields.terminalLocationHelp',
          visible: (form) => !!form.is_terminal,
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
    is_superuser: false,
    is_terminal: false,
    terminal_location: null,
    teams: [],
    roles: [],
    is_active: true,
    approval_exempt: false,
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
    is_superuser: u.is_superuser,
    is_terminal: u.is_terminal,
    terminal_location: u.terminal_location?.id ?? null,
    teams: u.teams.map((t) => t.id),
    roles: u.roles.map((r) => r.id),
    is_active: u.is_active,
    approval_exempt: u.approval_exempt,
  }),
})
