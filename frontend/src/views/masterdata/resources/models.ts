import { CopyPlus } from '@lucide/vue'
import { h } from 'vue'

import type { Schemas } from '@/api/types'

import { teamsApi } from '@/api/accounts'
import {
  assetModelsApi,
  categoriesApi,
  manufacturersApi,
  numberSequencesApi,
  suppliersApi,
} from '@/api/masterdata'
import { bool, mono, ownOrInherited } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { numberSequenceHints } from '@/components/masterdata/numberSequenceHints'
import { i18n } from '@/i18n'
import { categoryIcon } from '@/utils/icons'
import { modelLabel } from '@/utils/models'

const { n, t } = i18n.global

export default defineResource<Schemas['AssetModelOut']>({
  key: 'models',
  permission: 'models',
  // Sections per category, hardware before software.
  groupings: [
    {
      key: 'category',
      label: 'masterdata.fields.category',
      ordering: 'category__kind,category__sort_order,category__name',
      rowKey: (m) => m.category.id,
      rowLabel: (m) => [h(categoryIcon(m.category.icon), { size: 14 }), m.category.name],
    },
    {
      key: 'manufacturer',
      label: 'masterdata.fields.manufacturer',
      ordering: 'manufacturer__name',
      rowKey: (m) => m.manufacturer.id,
      rowLabel: (m) => m.manufacturer.name,
    },
  ],
  api: assetModelsApi,
  ordering: 'manufacturer__name',
  title: modelLabel,
  // A successor starts as a copy of what stays the same: who makes, numbers, buys and supports it.
  derive: {
    label: 'masterdata.createSuccessor',
    icon: CopyPlus,
    link: 'predecessor',
    copy: [
      'manufacturer',
      'category',
      'tracking',
      'number_sequence',
      'default_supplier',
      'warranty_months',
      'team',
      'is_requestable',
      'compatible_with',
    ],
  },
  columns: [
    {
      key: 'name',
      label: 'common.name',
      sorter: 'name',
      render: (m) =>
        h('div', [
          h('div', m.name),
          h('small', { class: 'muted' }, `${m.manufacturer.name} · ${m.designation}`),
        ]),
    },
    {
      key: 'category',
      label: 'masterdata.fields.category',
      sorter: 'category__name',
      width: 170,
      render: (m) => m.category.name,
    },
    {
      key: 'number_sequence',
      hidden: true,
      label: 'masterdata.fields.numberSequence',
      width: 170,
      render: (m) =>
        ownOrInherited(
          m.number_sequence?.name,
          m.effective_number_sequence?.name,
          t('masterdata.fields.inheritedSequence'),
        ),
    },
    {
      key: 'team',
      hidden: true,
      label: 'masterdata.fields.responsibleTeam',
      width: 160,
      render: (m) =>
        ownOrInherited(
          m.team?.name,
          m.effective_team?.name,
          t('masterdata.fields.inheritedModelTeam'),
        ),
    },
    {
      key: 'tracking',
      label: 'masterdata.fields.tracking',
      width: 150,
      render: (m) => t(`enums.tracking.${m.tracking}`),
    },
    {
      key: 'part_number',
      label: 'masterdata.fields.partNumber',
      sorter: 'part_number',
      width: 150,
      render: (m) => mono(m.part_number),
    },
    {
      key: 'ean',
      hidden: true,
      label: 'masterdata.fields.ean',
      width: 150,
      render: (m) => mono(m.ean),
    },
    {
      key: 'list_price',
      hidden: true,
      label: 'masterdata.fields.listPrice',
      width: 110,
      render: (m) => mono(m.list_price ? n(Number(m.list_price), 'currency') : null),
    },
    {
      key: 'is_requestable',
      label: 'masterdata.fields.requestableShort',
      width: 110,
      render: (m) => bool(m.is_requestable),
    },
    { key: 'is_active', label: 'common.active', width: 80, render: (m) => bool(m.is_active) },
    // Further columns to show from the column settings.
    {
      key: 'manufacturer',
      label: 'masterdata.fields.manufacturer',
      hidden: true,
      width: 150,
      render: (m) => m.manufacturer.name,
    },
    {
      key: 'designation',
      label: 'masterdata.fields.designation',
      hidden: true,
      width: 170,
      render: (m) => mono(m.designation),
    },
    {
      key: 'default_supplier',
      label: 'masterdata.fields.defaultSupplier',
      hidden: true,
      width: 170,
      render: (m) => m.default_supplier?.name ?? '—',
    },
    {
      key: 'warranty_months',
      label: 'masterdata.fields.warrantyMonths',
      hidden: true,
      width: 140,
      render: (m) => mono(m.warranty_months),
    },
  ],
  filters: [
    {
      key: 'category',
      label: 'masterdata.fields.category',
      type: 'entity',
      fetcher: categoriesApi.list,
      display: (c: Schemas['CategoryOut']) => c.path.join(' / '),
    },
    {
      key: 'manufacturer',
      label: 'masterdata.fields.manufacturer',
      type: 'entity',
      fetcher: manufacturersApi.list,
      display: (m: { name: string }) => m.name,
    },
    {
      key: 'tracking',
      label: 'masterdata.fields.tracking',
      type: 'enum',
      group: 'tracking',
      values: ['serialized', 'bulk', 'license'],
    },
    { key: 'is_active', label: 'common.active', type: 'boolean' },
  ],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true, span: 2 },
        {
          key: 'designation',
          label: 'masterdata.fields.designation',
          type: 'text',
          required: true,
          span: 2,
          help: 'masterdata.fields.designationHelp',
        },
        {
          key: 'manufacturer',
          label: 'masterdata.fields.manufacturer',
          type: 'entity',
          required: true,
          fetcher: manufacturersApi.list,
          display: (m: { name: string }) => m.name,
          initial: (m: Schemas['AssetModelOut']) => m.manufacturer,
        },
        {
          key: 'category',
          label: 'masterdata.fields.category',
          type: 'entity',
          required: true,
          fetcher: categoriesApi.list,
          display: (c: Schemas['CategoryOut']) => c.path.join(' / '),
          initial: (m: Schemas['AssetModelOut']) => ({ ...m.category, path: [m.category.name] }),
        },
        {
          key: 'tracking',
          label: 'masterdata.fields.tracking',
          type: 'enum',
          group: 'tracking',
          values: ['serialized', 'bulk', 'license'],
          help: 'masterdata.fields.trackingHelp',
        },
        { key: 'is_active', label: 'common.active', type: 'switch' },
      ],
    },
    {
      title: 'masterdata.sections.identification',
      fields: [
        { key: 'part_number', label: 'masterdata.fields.partNumber', type: 'mono' },
        { key: 'ean', label: 'masterdata.fields.ean', type: 'mono' },
      ],
    },
    {
      title: 'masterdata.sections.numbering',
      // Only individual devices get inventory numbers.
      visible: (form) => form.tracking === 'serialized',
      fields: [
        {
          key: 'number_sequence',
          label: 'masterdata.fields.numberSequence',
          type: 'entity',
          span: 2,
          help: 'masterdata.fields.modelNumberSequenceHelp',
          fetcher: numberSequencesApi.list,
          display: (s: { name: string; preview?: string }) =>
            s.preview ? `${s.name} · ${s.preview}` : s.name,
          initial: (m: Schemas['AssetModelOut']) => m.number_sequence,
        },
      ],
      extra: numberSequenceHints('category'),
    },
    {
      title: 'masterdata.sections.procurement',
      fields: [
        {
          key: 'default_supplier',
          label: 'masterdata.fields.defaultSupplier',
          type: 'entity',
          span: 2,
          fetcher: suppliersApi.list,
          display: (s: { name: string }) => s.name,
          initial: (m: Schemas['AssetModelOut']) => m.default_supplier,
        },
        {
          key: 'list_price',
          label: 'masterdata.fields.listPrice',
          type: 'number',
          min: 0,
          precision: 2,
        },
        {
          key: 'warranty_months',
          label: 'masterdata.fields.warrantyMonths',
          type: 'number',
          min: 0,
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
          help: 'masterdata.fields.modelTeamHelp',
          fetcher: teamsApi.list,
          display: (t: Schemas['TeamRefOut']) => t.name,
          initial: (m: Schemas['AssetModelOut']) => m.team,
        },
      ],
    },
    {
      title: 'masterdata.sections.portal',
      fields: [
        { key: 'is_requestable', label: 'masterdata.fields.requestable', type: 'switch', span: 2 },
      ],
    },
    {
      title: 'masterdata.sections.details',
      fields: [
        {
          key: 'predecessor',
          label: 'masterdata.fields.predecessor',
          type: 'entity',
          span: 2,
          help: 'masterdata.fields.predecessorHelp',
          fetcher: assetModelsApi.list,
          display: modelLabel,
          initial: (m: Schemas['AssetModelOut']) => m.predecessor,
        },
        {
          key: 'compatible_with',
          label: 'masterdata.fields.compatibleWith',
          type: 'entity',
          multiple: true,
          help: 'masterdata.fields.compatibleWithHelp',
          fetcher: assetModelsApi.list,
          display: modelLabel,
          initial: (m: Schemas['AssetModelOut']) => m.compatible_with,
        },
        { key: 'description', label: 'common.description', type: 'textarea' },
        { key: 'specifications', label: 'masterdata.fields.specifications', type: 'textarea' },
      ],
    },
  ],
  defaults: () => ({
    name: '',
    designation: '',
    manufacturer: null,
    category: null,
    part_number: '',
    ean: '',
    tracking: 'serialized',
    description: '',
    specifications: '',
    default_supplier: null,
    team: null,
    list_price: null,
    warranty_months: 24,
    compatible_with: [],
    predecessor: null,
    number_sequence: null,
    is_requestable: true,
    is_active: true,
  }),
  toForm: (m) => ({
    name: m.name,
    designation: m.designation,
    manufacturer: m.manufacturer.id,
    category: m.category.id,
    part_number: m.part_number,
    ean: m.ean,
    tracking: m.tracking,
    description: m.description,
    specifications: m.specifications,
    default_supplier: m.default_supplier?.id ?? null,
    team: m.team?.id ?? null,
    list_price: m.list_price ? Number(m.list_price) : null,
    warranty_months: m.warranty_months,
    compatible_with: m.compatible_with.map((c) => c.id),
    predecessor: m.predecessor?.id ?? null,
    number_sequence: m.number_sequence?.id ?? null,
    is_requestable: m.is_requestable,
    is_active: m.is_active,
  }),
})
