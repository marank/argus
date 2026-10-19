import { locationsApi } from '@/api/masterdata'
import { bool, mono } from '@/components/crud/cells'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'
import type { Location } from '@/types/masterdata'

const KINDS = ['site', 'building', 'room', 'storage']

export default defineResource<Location>({
  key: 'locations',
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
          display: (l: Location) => l.full_name,
          initial: (l: Location) => (l.parent ? { ...l.parent, full_name: l.parent.name } : null),
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
