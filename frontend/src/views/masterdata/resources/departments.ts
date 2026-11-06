import type { Schemas } from '@/api/types'
import { departmentsApi, usersApi } from '@/api/accounts'
import { mono, ownOrInherited, path, withIcon } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'
import { DEPARTMENT_ICONS, departmentIcon } from '@/utils/icons'

const { t } = i18n.global

const names = (users: Schemas['UserRefOut'][]) => users.map((u) => u.display_name).join(', ')

export default defineResource<Schemas['DepartmentOut']>({
  key: 'departments',
  permission: 'departments',
  api: departmentsApi,
  // Each department followed by its subdepartments.
  ordering: 'tree_position',
  tree: {
    ordering: 'tree_position',
    parent: (d) => d.parent?.id,
    label: (d) => withIcon(d.icon, d.name, departmentIcon),
  },
  title: (d) => d.name,
  columns: [
    {
      key: 'name',
      label: 'common.name',
      sorter: 'name',
      render: (d) => withIcon(d.icon, path(d.path), departmentIcon),
    },
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
      key: 'approvers',
      label: 'masterdata.fields.approvers',
      render: (d) =>
        ownOrInherited(
          names(d.approvers),
          names(d.effective_approvers),
          t('masterdata.fields.inheritedFromParentDepartment'),
        ),
    },
    {
      key: 'sort_order',
      hidden: true,
      label: 'masterdata.fields.sortOrder',
      sorter: 'sort_order',
      width: 110,
      render: (d) => mono(d.sort_order),
    },
  ],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true },
        {
          key: 'icon',
          label: 'masterdata.fields.icon',
          type: 'icon',
          icons: DEPARTMENT_ICONS,
          group: 'departmentIcon',
          required: true,
        },
        { key: 'code', label: 'common.code', type: 'mono' },
        { key: 'cost_center', label: 'masterdata.fields.costCenter', type: 'mono' },
        {
          key: 'parent',
          label: 'masterdata.fields.parent',
          type: 'entity',
          fetcher: departmentsApi.list,
          // The edited row's parent comes as a bare reference, without the path.
          display: (d: Schemas['DepartmentOut']) => d.path?.join(' / ') ?? d.name,
          initial: (d: Schemas['DepartmentOut']) => d.parent,
        },
        {
          key: 'sort_order',
          label: 'masterdata.fields.sortOrder',
          type: 'number',
          min: 0,
          help: 'masterdata.fields.departmentSortHelp',
        },
        {
          key: 'approvers',
          label: 'masterdata.fields.approvers',
          type: 'entity',
          multiple: true,
          span: 2,
          fetcher: usersApi.list,
          params: { is_active: true },
          display: (u: Schemas['UserRefOut']) => u.display_name,
          initial: (d: Schemas['DepartmentOut']) => d.approvers,
          help: 'masterdata.fields.approversHelp',
        },
      ],
    },
  ],
  defaults: () => ({
    name: '',
    icon: 'building',
    code: '',
    cost_center: '',
    parent: null,
    sort_order: 0,
    approvers: [],
  }),
  toForm: (d) => ({
    name: d.name,
    icon: d.icon,
    code: d.code,
    cost_center: d.cost_center,
    parent: d.parent?.id ?? null,
    sort_order: d.sort_order,
    approvers: d.approvers.map((a) => a.id),
  }),
})
