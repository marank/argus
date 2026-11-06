import type { Schemas } from '@/api/types'
import { MapPin } from '@lucide/vue'
import { h } from 'vue'

import { locationsApi } from '@/api/masterdata'
import { bool, mono } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'

const KINDS = ['site', 'building', 'room', 'storage']
const siteOf = (l: Schemas['LocationOut']) => l.full_name.split(' / ')[0] ?? l.name

export default defineResource<Schemas['LocationOut']>({
  key: 'locations',
  permission: 'locations',
  // Sections per site (the top-level location).
  groupings: [
    {
      key: 'site',
      label: 'masterdata.fields.site',
      ordering: 'site',
      rowKey: (l) => siteOf(l),
      rowLabel: (l) => [h(MapPin, { size: 14 }), siteOf(l)],
    },
  ],
  api: locationsApi,
  ordering: 'name',
  title: (l) => l.full_name,
  columns: [
    { key: 'name', label: 'common.name', sorter: 'name', render: (l) => l.full_name },
    { key: 'code', label: 'common.code', sorter: 'code', width: 140, render: (l) => mono(l.code) },
    {
      key: 'kind',
      label: 'masterdata.fields.kind',
      sorter: 'kind',
      width: 130,
      render: (l) => i18n.global.t(`enums.locationKind.${l.kind}`),
    },
    {
      key: 'is_pickup_point',
      label: 'masterdata.fields.pickupPoint',
      width: 120,
      render: (l) => bool(l.is_pickup_point),
    },
    // Further columns to show from the column settings.
    {
      key: 'description',
      label: 'common.description',
      hidden: true,
      render: (l) => l.description || '—',
    },
  ],
  filters: [
    {
      key: 'kind',
      label: 'masterdata.fields.kind',
      type: 'enum',
      group: 'locationKind',
      values: KINDS,
    },
    { key: 'is_pickup_point', label: 'masterdata.fields.pickupPoint', type: 'boolean' },
  ],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true },
        { key: 'code', label: 'common.code', type: 'mono' },
        {
          key: 'kind',
          label: 'masterdata.fields.kind',
          type: 'enum',
          group: 'locationKind',
          values: KINDS,
        },
        {
          key: 'parent',
          label: 'masterdata.fields.parent',
          type: 'entity',
          fetcher: locationsApi.list,
          display: (l: Schemas['LocationOut']) => l.full_name,
          initial: (l: Schemas['LocationOut']) =>
            l.parent ? { ...l.parent, full_name: l.parent.name } : null,
        },
        {
          key: 'is_pickup_point',
          label: 'masterdata.fields.pickupPoint',
          type: 'switch',
          span: 2,
          help: 'masterdata.fields.pickupPointHelp',
        },
      ],
    },
    {
      title: 'masterdata.sections.notes',
      fields: [{ key: 'description', label: 'common.description', type: 'textarea' }],
    },
  ],
  defaults: () => ({
    name: '',
    code: '',
    kind: 'room',
    parent: null,
    description: '',
    is_pickup_point: false,
  }),
  toForm: (l) => ({
    name: l.name,
    code: l.code,
    kind: l.kind,
    parent: l.parent?.id ?? null,
    description: l.description,
    is_pickup_point: l.is_pickup_point,
  }),
})
