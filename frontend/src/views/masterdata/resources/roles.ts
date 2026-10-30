import type { Schemas } from '@/api/types'
import { rolesApi, usersApi } from '@/api/accounts'
import { text } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import PermissionMatrix from '@/components/masterdata/PermissionMatrix.vue'
import { i18n } from '@/i18n'

/** Count of areas per level, e.g. "3 write · 5 read". */
function summary(role: Schemas['RoleOut']): string {
  const levels = Object.values(role.permissions)
  const write = levels.filter((l) => l === 'write').length
  const read = levels.filter((l) => l === 'read').length
  return i18n.global.t('masterdata.roles.summary', { write, read })
}

export default defineResource<Schemas['RoleOut']>({
  key: 'roles',
  // Who may change what is decided by administrators only.
  superuser: true,
  api: rolesApi,
  ordering: 'name',
  title: (r) => r.name,
  columns: [
    { key: 'name', label: 'common.name', sorter: 'name', width: 200 },
    { key: 'description', label: 'common.description', render: (r) => text(r.description) },
    { key: 'permissions', label: 'masterdata.roles.permissions', width: 200, render: summary },
    {
      key: 'members',
      label: 'masterdata.fields.members',
      render: (r) => text(r.members.map((m) => m.display_name).join(', ')),
    },
  ],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true, span: 2 },
        { key: 'description', label: 'common.description', type: 'textarea' },
        {
          key: 'members',
          label: 'masterdata.fields.members',
          type: 'entity',
          multiple: true,
          fetcher: usersApi.list,
          params: { is_staff: true, is_active: true },
          display: (u: Schemas['UserRefOut']) => u.display_name,
          initial: (r: Schemas['RoleOut']) => r.members,
          help: 'masterdata.roles.membersHelp',
        },
      ],
      extra: PermissionMatrix,
    },
  ],
  defaults: () => ({ name: '', description: '', permissions: {}, members: [] }),
  toForm: (r) => ({
    name: r.name,
    description: r.description,
    permissions: { ...r.permissions },
    members: r.members.map((m) => m.id),
  }),
})
