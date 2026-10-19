import { h } from 'vue'

import { assetModelsApi, categoriesApi, manufacturersApi, suppliersApi } from '@/api/masterdata'
import { bool, mono } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'
import type { AssetModel, Category } from '@/types/masterdata'

const { n, t } = i18n.global

export default defineResource<AssetModel>({
  key: 'models',
  api: assetModelsApi,
  ordering: 'manufacturer__name',
  title: (m) => m.full_name,
  columns: [
    {
      key: 'name',
      label: 'common.name',
      sorter: 'name',
      render: (m) =>
        h('div', [h('div', m.name), h('small', { class: 'muted' }, m.manufacturer.name)]),
    },
    {
      key: 'category',
      label: 'masterdata.fields.category',
      sorter: 'category__name',
      width: 170,
      render: (m) => m.category.name,
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
    { key: 'ean', label: 'masterdata.fields.ean', width: 150, render: (m) => mono(m.ean) },
    {
      key: 'list_price',
      label: 'masterdata.fields.listPrice',
      width: 110,
      render: (m) => mono(m.list_price ? n(Number(m.list_price), 'currency') : null),
    },
    {
      key: 'is_requestable',
      label: 'masterdata.fields.requestable',
      width: 110,
      render: (m) => bool(m.is_requestable),
    },
    { key: 'is_active', label: 'common.active', width: 80, render: (m) => bool(m.is_active) },
  ],
  filters: [
    {
      key: 'category',
      label: 'masterdata.fields.category',
      type: 'entity',
      fetcher: categoriesApi.list,
      display: (c: Category) => c.path.join(' / '),
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
      values: ['serialized', 'bulk'],
    },
    { key: 'is_active', label: 'common.active', type: 'boolean' },
  ],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true, span: 2 },
        {
          key: 'manufacturer',
          label: 'masterdata.fields.manufacturer',
          type: 'entity',
          required: true,
          fetcher: manufacturersApi.list,
          display: (m: { name: string }) => m.name,
          initial: (m: AssetModel) => m.manufacturer,
        },
        {
          key: 'category',
          label: 'masterdata.fields.category',
          type: 'entity',
          required: true,
          fetcher: categoriesApi.list,
          display: (c: Category) => c.path.join(' / '),
          initial: (m: AssetModel) => ({ ...m.category, path: [m.category.name] }),
        },
        {
          key: 'tracking',
          label: 'masterdata.fields.tracking',
          type: 'enum',
          group: 'tracking',
          values: ['serialized', 'bulk'],
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
      title: 'masterdata.sections.procurement',
      fields: [
        {
          key: 'default_supplier',
          label: 'masterdata.fields.defaultSupplier',
          type: 'entity',
          span: 2,
          fetcher: suppliersApi.list,
          display: (s: { name: string }) => s.name,
          initial: (m: AssetModel) => m.default_supplier,
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
      title: 'masterdata.sections.portal',
      fields: [
        { key: 'is_requestable', label: 'masterdata.fields.requestable', type: 'switch', span: 2 },
      ],
    },
    {
      title: 'masterdata.sections.details',
      fields: [
        {
          key: 'compatible_with',
          label: 'masterdata.fields.compatibleWith',
          type: 'entity',
          multiple: true,
          help: 'masterdata.fields.compatibleWithHelp',
          fetcher: assetModelsApi.list,
          display: (m: AssetModel) => m.full_name,
          initial: (m: AssetModel) => m.compatible_with,
        },
        { key: 'description', label: 'common.description', type: 'textarea' },
        { key: 'specifications', label: 'masterdata.fields.specifications', type: 'textarea' },
      ],
    },
  ],
  defaults: () => ({
    name: '',
    manufacturer: null,
    category: null,
    part_number: '',
    ean: '',
    tracking: 'serialized',
    description: '',
    specifications: '',
    default_supplier: null,
    list_price: null,
    warranty_months: 24,
    compatible_with: [],
    is_requestable: true,
    is_active: true,
  }),
  toForm: (m) => ({
    name: m.name,
    manufacturer: m.manufacturer.id,
    category: m.category.id,
    part_number: m.part_number,
    ean: m.ean,
    tracking: m.tracking,
    description: m.description,
    specifications: m.specifications,
    default_supplier: m.default_supplier?.id ?? null,
    list_price: m.list_price ? Number(m.list_price) : null,
    warranty_months: m.warranty_months,
    compatible_with: m.compatible_with.map((c) => c.id),
    is_requestable: m.is_requestable,
    is_active: m.is_active,
  }),
})
