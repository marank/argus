import { teamsApi, usersApi } from '@/api/accounts'
import { mono, text } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { useFeaturesStore } from '@/stores/features'
import type { Team, UserRef } from '@/types/accounts'

// The LDAP group only means something while directory login is on.
const ldapEnabled = () => useFeaturesStore().ldapEnabled

export default defineResource<Team>({
  key: 'teams',
  api: teamsApi,
  ordering: 'sort_order',
  title: (team) => team.name,
  columns: [
    { key: 'name', label: 'common.name', sorter: 'name' },
    { key: 'code', label: 'common.code', sorter: 'code', width: 120, render: (t) => mono(t.code) },
    {
      key: 'members',
      label: 'masterdata.fields.members',
      render: (t) => text(t.members.map((m) => m.display_name).join(', ')),
    },
    {
      key: 'ldap_group_dn',
      label: 'masterdata.fields.ldapGroup',
      render: (t) => mono(t.ldap_group_dn),
      visible: ldapEnabled,
    },
    {
      key: 'sort_order',
      label: 'masterdata.fields.sortOrder',
      sorter: 'sort_order',
      width: 110,
      render: (t) => mono(t.sort_order),
    },
  ],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true, span: 2 },
        { key: 'code', label: 'common.code', type: 'mono' },
        {
          key: 'sort_order',
          label: 'masterdata.fields.sortOrder',
          type: 'number',
          min: 0,
          help: 'masterdata.fields.departmentSortHelp',
        },
        {
          key: 'members',
          label: 'masterdata.fields.members',
          type: 'entity',
          multiple: true,
          fetcher: usersApi.list,
          params: { is_staff: true, is_active: true },
          display: (u: UserRef) => u.display_name,
          initial: (t: Team) => t.members,
        },
        {
          key: 'ldap_group_dn',
          label: 'masterdata.fields.ldapGroup',
          type: 'mono',
          span: 2,
          help: 'masterdata.fields.ldapGroupHelp',
          visible: ldapEnabled,
        },
      ],
    },
  ],
  defaults: () => ({ name: '', code: '', sort_order: 0, ldap_group_dn: '', members: [] }),
  toForm: (t) => ({
    name: t.name,
    code: t.code,
    sort_order: t.sort_order,
    ldap_group_dn: t.ldap_group_dn,
    members: t.members.map((m) => m.id),
  }),
})
