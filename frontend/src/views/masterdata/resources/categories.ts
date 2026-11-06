import { AppWindow, Check, Cpu } from '@lucide/vue'
import { h } from 'vue'

import { teamsApi } from '@/api/accounts'
import { categoriesApi, numberSequencesApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import { bool, inherited, mono, ownOrInherited, path, withIcon } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { numberSequenceHints } from '@/components/masterdata/numberSequenceHints'
import { i18n } from '@/i18n'
import { CATEGORY_KINDS, MODEL_CHOICES } from '@/types/masterdata'

const { t } = i18n.global

export default defineResource<Schemas['CategoryOut']>({
  key: 'categories',
  permission: 'categories',
  api: categoriesApi,
  // Each category followed by its subcategories.
  ordering: 'tree_position',
  // Hardware first, then software (alphabetical order of the stored values).
  groupings: [
    {
      key: 'kind',
      label: 'masterdata.fields.kind',
      ordering: 'kind',
      rowKey: (c) => c.kind,
      rowLabel: (c) => [
        h(c.kind === 'software' ? AppWindow : Cpu, { size: 14 }),
        t(`enums.categoryKind.${c.kind}`),
      ],
    },
  ],
  tree: {
    ordering: 'tree_position',
    parent: (c) => c.parent?.id,
    label: (c) => withIcon(c.icon, c.name),
  },
  title: (c) => c.name,
  columns: [
    {
      key: 'name',
      label: 'common.name',
      sorter: 'name',
      render: (c) => withIcon(c.icon, path(c.path)),
    },
    { key: 'code', label: 'common.code', sorter: 'code', width: 160, render: (c) => mono(c.code) },
    {
      key: 'number_sequence',
      hidden: true,
      label: 'masterdata.fields.numberSequence',
      width: 200,
      render: (c) => c.number_sequence?.name ?? '—',
    },
    {
      key: 'team',
      label: 'masterdata.fields.responsibleTeam',
      width: 160,
      render: (c) =>
        ownOrInherited(
          c.team?.name,
          c.effective_team?.name,
          t('masterdata.fields.inheritedCategoryTeam'),
        ),
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
      render: (c) =>
        !c.requires_approval && c.needs_approval
          ? inherited(h(Check, { size: 15 }), t('masterdata.fields.inheritedFromParent'))
          : bool(c.requires_approval),
    },
    {
      key: 'sort_order',
      hidden: true,
      label: 'masterdata.fields.sortOrder',
      sorter: 'sort_order',
      width: 110,
      render: (c) => mono(c.sort_order),
    },
    // Further columns to show from the column settings.
    {
      key: 'kind',
      label: 'masterdata.fields.kind',
      hidden: true,
      width: 110,
      render: (c) => t(`enums.categoryKind.${c.kind}`),
    },
    {
      key: 'item_name',
      label: 'masterdata.fields.itemName',
      hidden: true,
      width: 150,
      render: (c) => c.item_name || '—',
    },
    {
      key: 'identifier_label',
      label: 'masterdata.fields.identifierLabel',
      hidden: true,
      width: 170,
      render: (c) => c.identifier_label || '—',
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
          key: 'identifier_label',
          label: 'masterdata.fields.identifierLabel',
          type: 'text',
          help: 'masterdata.fields.identifierLabelHelp',
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
          // The edited row's parent comes as a bare reference, without the path.
          display: (c: Schemas['CategoryOut']) => c.path?.join(' / ') ?? c.name,
          initial: (c: Schemas['CategoryOut']) => c.parent,
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
          initial: (c: Schemas['CategoryOut']) => c.number_sequence,
        },
      ],
      extra: numberSequenceHints('parent'),
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
          display: (t: Schemas['TeamRefOut']) => t.name,
          initial: (c: Schemas['CategoryOut']) => c.team,
        },
      ],
    },
    {
      title: 'masterdata.sections.portal',
      fields: [
        { key: 'is_requestable', label: 'masterdata.fields.requestable', type: 'switch' },
        {
          key: 'model_choice',
          label: 'masterdata.fields.modelChoice',
          type: 'enum',
          group: 'modelChoice',
          values: MODEL_CHOICES,
          required: true,
          span: 2,
          help: 'masterdata.fields.modelChoiceHelp',
        },
        {
          key: 'requires_approval',
          label: 'masterdata.fields.requiresApproval',
          type: 'switch',
          help: 'masterdata.fields.requiresApprovalHelp',
        },
        {
          key: 'is_accessory',
          label: 'masterdata.fields.isAccessory',
          type: 'switch',
          help: 'masterdata.fields.isAccessoryHelp',
        },
        { key: 'sort_order', label: 'masterdata.fields.sortOrder', type: 'number', min: 0 },
      ],
    },
  ],
  defaults: () => ({
    name: '',
    item_name: '',
    identifier_label: '',
    kind: 'hardware',
    code: '',
    parent: null,
    description: '',
    icon: '',
    number_sequence: null,
    team: null,
    is_requestable: true,
    model_choice: 'any_or_specific',
    requires_approval: false,
    is_accessory: false,
    sort_order: 0,
  }),
  toForm: (c) => ({
    name: c.name,
    item_name: c.item_name,
    identifier_label: c.identifier_label,
    kind: c.kind,
    code: c.code,
    parent: c.parent?.id ?? null,
    description: c.description,
    icon: c.icon,
    number_sequence: c.number_sequence?.id ?? null,
    team: c.team?.id ?? null,
    is_requestable: c.is_requestable,
    model_choice: c.model_choice,
    requires_approval: c.requires_approval,
    is_accessory: c.is_accessory,
    sort_order: c.sort_order,
  }),
})
