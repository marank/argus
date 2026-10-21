import { AppWindow, Cpu } from '@lucide/vue'
import { h } from 'vue'

import { teamsApi } from '@/api/accounts'
import { categoriesApi, numberSequencesApi } from '@/api/masterdata'
import { bool, mono, withIcon } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'
import type { TeamRef } from '@/types/accounts'
import { CATEGORY_KINDS, type Category } from '@/types/masterdata'

const { t } = i18n.global

export default defineResource<Category>({
  key: 'categories',
  permission: 'categories',
  api: categoriesApi,
  ordering: 'sort_order',
  // Hardware first, then software (alphabetical order of the stored values).
  groupBy: {
    ordering: 'kind',
    key: (c) => c.kind,
    label: (c) => [
      h(c.kind === 'software' ? AppWindow : Cpu, { size: 14 }),
      t(`enums.categoryKind.${c.kind}`),
    ],
  },
  title: (c) => c.name,
  columns: [
    {
      key: 'name',
      label: 'common.name',
      sorter: 'name',
      render: (c) => withIcon(c.icon, c.path.join(' / ')),
    },
    { key: 'code', label: 'common.code', sorter: 'code', width: 160, render: (c) => mono(c.code) },
    {
      key: 'number_sequence',
      label: 'masterdata.fields.numberSequence',
      width: 200,
      render: (c) => c.number_sequence?.name ?? '—',
    },
    {
      key: 'team',
      label: 'masterdata.fields.responsibleTeam',
      width: 160,
      render: (c) => c.team?.name ?? '—',
    },
    {
      key: 'is_requestable',
      label: 'masterdata.fields.requestable',
      width: 150,
      render: (c) => bool(c.is_requestable),
    },
    {
      key: 'requires_approval',
      label: 'masterdata.fields.requiresApproval',
      width: 170,
      render: (c) => bool(c.requires_approval),
    },
    {
      key: 'sort_order',
      label: 'masterdata.fields.sortOrder',
      sorter: 'sort_order',
      width: 110,
      render: (c) => mono(c.sort_order),
    },
  ],
  filters: [
    {
      key: 'kind',
      label: 'masterdata.fields.categoryKind',
      type: 'enum',
      group: 'categoryKind',
      values: CATEGORY_KINDS,
    },
    { key: 'is_requestable', label: 'masterdata.fields.requestable', type: 'boolean' },
  ],
  sections: [
    {
      fields: [
        {
          key: 'name',
          label: 'masterdata.fields.categoryName',
          type: 'text',
          required: true,
          help: 'masterdata.fields.categoryNameHelp',
        },
        { key: 'code', label: 'common.code', type: 'mono' },
        {
          key: 'item_name',
          label: 'masterdata.fields.itemName',
          type: 'text',
          help: 'masterdata.fields.itemNameHelp',
        },
        {
          key: 'kind',
          label: 'masterdata.fields.categoryKind',
          type: 'enum',
          group: 'categoryKind',
          values: CATEGORY_KINDS,
          required: true,
          help: 'masterdata.fields.categoryKindHelp',
        },
        {
          key: 'parent',
          label: 'masterdata.fields.parent',
          type: 'entity',
          fetcher: categoriesApi.list,
          display: (c: Category) => c.path.join(' / '),
          initial: (c: Category) => c.parent,
        },
        { key: 'icon', label: 'masterdata.fields.icon', type: 'icon' },
        { key: 'description', label: 'common.description', type: 'textarea' },
      ],
    },
    {
      title: 'masterdata.sections.numbering',
      fields: [
        {
          key: 'number_sequence',
          label: 'masterdata.fields.numberSequence',
          type: 'entity',
          span: 2,
          help: 'masterdata.fields.numberSequenceHelp',
          fetcher: numberSequencesApi.list,
          display: (s: { name: string; preview?: string }) =>
            s.preview ? `${s.name} · ${s.preview}` : s.name,
          initial: (c: Category) => c.number_sequence,
        },
      ],
    },
    {
      title: 'masterdata.sections.responsibility',
      fields: [
        {
          key: 'team',
          label: 'masterdata.fields.responsibleTeam',
          type: 'entity',
          span: 2,
          help: 'masterdata.fields.categoryTeamHelp',
          fetcher: teamsApi.list,
          display: (t: TeamRef) => t.name,
          initial: (c: Category) => c.team,
        },
      ],
    },
    {
      title: 'masterdata.sections.portal',
      fields: [
        { key: 'is_requestable', label: 'masterdata.fields.requestable', type: 'switch' },
        {
          key: 'allow_any_model',
          label: 'masterdata.fields.allowAnyModel',
          type: 'switch',
          help: 'masterdata.fields.allowAnyModelHelp',
        },
        {
          key: 'requires_approval',
          label: 'masterdata.fields.requiresApproval',
          type: 'switch',
          help: 'masterdata.fields.requiresApprovalHelp',
        },
        { key: 'sort_order', label: 'masterdata.fields.sortOrder', type: 'number', min: 0 },
      ],
    },
  ],
  defaults: () => ({
    name: '',
    item_name: '',
    kind: 'hardware',
    code: '',
    parent: null,
    description: '',
    icon: '',
    number_sequence: null,
    team: null,
    is_requestable: true,
    allow_any_model: true,
    requires_approval: false,
    sort_order: 0,
  }),
  toForm: (c) => ({
    name: c.name,
    item_name: c.item_name,
    kind: c.kind,
    code: c.code,
    parent: c.parent?.id ?? null,
    description: c.description,
    icon: c.icon,
    number_sequence: c.number_sequence?.id ?? null,
    team: c.team?.id ?? null,
    is_requestable: c.is_requestable,
    allow_any_model: c.allow_any_model,
    requires_approval: c.requires_approval,
    sort_order: c.sort_order,
  }),
})
