import { h } from 'vue'

import { numberSequencesApi } from '@/api/masterdata'
import { mono } from '@/components/crud/cells'
import NumberSequencePreview from '@/components/masterdata/NumberSequencePreview.vue'
import { defineResource } from '@/components/crud/types'
import { i18n } from '@/i18n'
import type { NumberSequence } from '@/types/masterdata'

export default defineResource<NumberSequence>({
  key: 'numberSequences',
  permission: 'number_sequences',
  api: numberSequencesApi,
  ordering: 'name',
  title: (s) => s.name,
  columns: [
    { key: 'name', label: 'common.name', sorter: 'name' },
    { key: 'code', label: 'common.code', sorter: 'code', width: 180, render: (s) => mono(s.code) },
    {
      key: 'pattern',
      label: 'masterdata.fields.pattern',
      width: 200,
      render: (s) => mono(s.pattern),
    },
    {
      key: 'reset_period',
      label: 'masterdata.fields.resetPeriod',
      width: 120,
      render: (s) => i18n.global.t(`enums.resetPeriod.${s.reset_period}`),
    },
    {
      key: 'preview',
      label: 'masterdata.fields.preview',
      width: 180,
      render: (s) =>
        h(
          'span',
          { class: 'mono', style: 'color: var(--ar-primary); font-weight: 600' },
          s.preview,
        ),
    },
  ],
  sections: [
    {
      fields: [
        { key: 'name', label: 'common.name', type: 'text', required: true },
        {
          key: 'code',
          label: 'common.code',
          type: 'mono',
          required: true,
          help: 'masterdata.fields.sequenceCodeHelp',
        },
      ],
    },
    {
      title: 'masterdata.sections.format',
      fields: [
        { key: 'prefix', label: 'masterdata.fields.prefix', type: 'mono' },
        {
          key: 'pattern',
          label: 'masterdata.fields.pattern',
          type: 'mono',
          required: true,
          help: 'masterdata.fields.patternHelp',
        },
        { key: 'padding', label: 'masterdata.fields.padding', type: 'number', min: 1, max: 12 },
        {
          key: 'reset_period',
          label: 'masterdata.fields.resetPeriod',
          type: 'enum',
          group: 'resetPeriod',
          values: ['never', 'yearly', 'monthly'],
        },
        { key: 'next_value', label: 'masterdata.fields.nextValue', type: 'number', min: 1 },
      ],
      extra: NumberSequencePreview,
    },
  ],
  defaults: () => ({
    name: '',
    code: '',
    prefix: '',
    pattern: '{prefix}{year}-{seq}',
    padding: 4,
    next_value: 1,
    reset_period: 'never',
  }),
  toForm: ({ id: _id, preview: _preview, ...rest }) => rest,
})
