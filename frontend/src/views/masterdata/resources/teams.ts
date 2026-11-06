import type { Schemas } from '@/api/types'
import { teamsApi, usersApi } from '@/api/accounts'
import { bool, mono, text } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { useFeaturesStore } from '@/stores/features'

// The LDAP group only means something while directory login is on.
const ldapEnabled = () => useFeaturesStore().ldapEnabled

export default defineResource<Schemas['TeamOut']>({
  key: 'teams',
  permission: 'teams',
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
      key: 'is_default',
      label: 'masterdata.fields.defaultTeam',
      width: 120,
      render: (t) => bool(t.is_default),
    },
    {
      key: 'ldap_group_dn',
      hidden: true,
      label: 'masterdata.fields.ldapGroup',
      render: (t) => mono(t.ldap_group_dn),
      visible: ldapEnabled,
    },
    {
      key: 'sort_order',
      hidden: true,
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
          display: (u: Schemas['UserRefOut']) => u.display_name,
          initial: (t: Schemas['TeamOut']) => t.members,
        },
        {
          key: 'ldap_group_dn',
          label: 'masterdata.fields.ldapGroup',
          type: 'mono',
          span: 2,
          help: 'masterdata.fields.ldapGroupHelp',
          visible: ldapEnabled,
        },
        {
          key: 'is_default',
          label: 'masterdata.fields.defaultTeam',
          type: 'switch',
          help: 'masterdata.fields.defaultTeamHelp',
        },
      ],
    },
  ],
  defaults: () => ({
    name: '',
    code: '',
    sort_order: 0,
    ldap_group_dn: '',
    is_default: false,
    members: [],
  }),
  toForm: (t) => ({
    name: t.name,
    code: t.code,
    sort_order: t.sort_order,
    ldap_group_dn: t.ldap_group_dn,
    is_default: t.is_default,
    members: t.members.map((m) => m.id),
  }),
})
