<script setup lang="ts">
import { modelLabel } from '@/utils/models'
import { FileUp } from '@lucide/vue'
import {
  NAlert,
  NButton,
  NDataTable,
  NModal,
  NRadioButton,
  NRadioGroup,
  NSelect,
  NStep,
  NSteps,
  NTag,
  NText,
  type DataTableColumns,
} from 'naive-ui'
import { computed, h, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { assetsApi } from '@/api/inventory'
import { assetModelsApi, locationsApi } from '@/api/masterdata'
import type { Schemas } from '@/api/types'
import EntitySelect from '@/components/common/EntitySelect.vue'
import FieldLabel from '@/components/common/FieldLabel.vue'
import ToggleRow from '@/components/common/ToggleRow.vue'
import { useAction } from '@/composables/useAction'
import { useFormat } from '@/composables/useFormat'
import { ASSET_CONDITIONS, ASSET_STATUSES } from '@/types/inventory'
import {
  FIELD_LABELS,
  IMPORT_FIELDS,
  IMPORT_MATCHES,
  loadSettings,
  mapRows,
  sampleValue,
  saveSettings,
  suggestMapping,
  emptyMapping,
  type ColumnMapping,
  type ImportField,
  type ImportMatch,
} from '@/utils/assetImport'
import {
  guessHasHeader,
  readTableFile,
  toTable,
  UnsupportedFileError,
  type Sheet,
} from '@/utils/tableFile'

type Result = Schemas['AssetImportResultOut']
type ResultRow = Schemas['AssetImportRowOut']
type Action = Schemas['ImportAction']
type Filter = 'all' | 'changes' | 'errors'

const show = defineModel<boolean>('show', { required: true })
const emit = defineEmits<{ imported: [] }>()
const { t } = useI18n()
const { enumLabel } = useFormat()
const { busy, run } = useAction()

const step = ref(1)
const fileName = ref('')
const sheets = ref<Sheet[]>([])
const sheetIndex = ref(0)
const hasHeader = ref(true)
const readError = ref('')
const fileInput = ref<HTMLInputElement | null>(null)

const mapping = ref<ColumnMapping>(emptyMapping())
const defaults = reactive<Schemas['AssetImportDefaultsIn']>({
  model: null,
  location: null,
  status: null,
  condition: null,
})
const NO_MATCH = 'none'
const matchBy = ref<ImportMatch | typeof NO_MATCH>('serial_number')
const existing = ref<Schemas['ExistingDevices']>('update')
const ignoreCase = ref(false)

const result = ref<Result | null>(null)
const imported = ref(false)
const filter = ref<Filter>('all')

function reset() {
  step.value = 1
  fileName.value = ''
  sheets.value = []
  readError.value = ''
  result.value = null
  imported.value = false
  filter.value = 'all'
}

watch(show, (open) => {
  if (open) reset()
})

async function onFile(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  readError.value = ''
  try {
    sheets.value = await readTableFile(file)
    // The first sheet that holds anything.
    const first = sheets.value.findIndex((s) => s.rows.some((r) => r.some((c) => c.trim())))
    selectSheet(Math.max(first, 0))
    if (!table.value!.rows.length) {
      sheets.value = []
      readError.value = t('inventory.import.emptyFile')
      return
    }
    fileName.value = file.name
    step.value = 2
  } catch (error) {
    readError.value = t(
      error instanceof UnsupportedFileError
        ? 'inventory.import.oldExcel'
        : 'inventory.import.unreadable',
    )
  }
}

const table = computed(() => {
  const sheet = sheets.value[sheetIndex.value]
  return sheet ? toTable(sheet.rows, hasHeader.value) : null
})

const sheetOptions = computed(() =>
  sheets.value.map((s, index) => ({ value: index, label: s.name })),
)

function selectSheet(index: number) {
  sheetIndex.value = index
  hasHeader.value = guessHasHeader(sheets.value[index]!.rows)
  applySettings(table.value!.headers)
}

function setHasHeader(value: boolean) {
  hasHeader.value = value
  applySettings(table.value!.headers)
}

/** The settings of the last import of a file with the same columns, or suggestions. */
// eslint-disable-next-line complexity -- a ?? default per stored setting, no branching logic
function applySettings(headers: string[]) {
  const stored = loadSettings(headers)
  mapping.value = stored?.mapping ?? suggestMapping(headers)
  Object.assign(defaults, {
    model: stored?.defaults.model ?? null,
    location: stored?.defaults.location ?? null,
    status: stored?.defaults.status ?? null,
    condition: stored?.defaults.condition ?? null,
  })
  matchBy.value = stored ? (stored.matchBy ?? NO_MATCH) : 'serial_number'
  existing.value = stored?.existing ?? 'update'
  ignoreCase.value = stored?.ignoreCase ?? false
}

const columnOptions = computed(() =>
  (table.value?.headers ?? []).map((header, index) => ({
    value: index,
    label:
      header ||
      [t('inventory.import.column', { number: index + 1 }), sampleValue(table.value!.rows, index)]
        .filter(Boolean)
        .join(' · '),
  })),
)

const mappedCount = computed(() =>
  table.value?.rows.length ? IMPORT_FIELDS.filter((f) => mapping.value[f] !== null).length : 0,
)
const modelMissing = computed(() => mapping.value.model === null && !defaults.model)

const fieldLabel = (field: ImportField) => t(FIELD_LABELS[field])

const matchOptions = computed(() => [
  ...IMPORT_MATCHES.map((m) => ({ value: m, label: fieldLabel(m) })),
  { value: NO_MATCH, label: t('inventory.import.noMatch') },
])

function payload(): Schemas['AssetImportIn'] {
  return {
    rows: mapRows(table.value!.rows, mapping.value),
    defaults: { ...defaults },
    match_by: matchBy.value === NO_MATCH ? null : matchBy.value,
    existing: existing.value,
    ignore_case: ignoreCase.value,
  }
}

async function preview() {
  const answer = await run(() => assetsApi.importPreview(payload()))
  if (!answer) return
  saveSettings(table.value!.headers, {
    mapping: mapping.value,
    defaults: { ...defaults },
    matchBy: matchBy.value === NO_MATCH ? null : matchBy.value,
    existing: existing.value,
    ignoreCase: ignoreCase.value,
  })
  result.value = answer
  filter.value = answer.failed ? 'errors' : 'all'
  step.value = 3
}

async function runImport() {
  const answer = await run(() => assetsApi.import(payload()))
  if (!answer) return
  result.value = answer
  imported.value = true
  filter.value = answer.failed ? 'errors' : 'changes'
  emit('imported')
}

const pending = computed(() => (result.value ? result.value.created + result.value.updated : 0))

const ACTION_TAGS: Record<Action, 'success' | 'info' | 'default' | 'warning' | 'error'> = {
  create: 'success',
  update: 'info',
  unchanged: 'default',
  skip: 'warning',
  error: 'error',
}

const visibleRows = computed(() => {
  const rows = result.value?.rows ?? []
  if (filter.value === 'errors') return rows.filter((r) => r.action === 'error')
  if (filter.value === 'changes')
    return rows.filter((r) => r.action === 'create' || r.action === 'update')
  return rows
})

const summary = computed(() => {
  const r = result.value
  if (!r) return []
  return (
    [
      ['create', r.created],
      ['update', r.updated],
      ['unchanged', r.unchanged],
      ['skip', r.skipped],
      ['error', r.failed],
    ] as [Action, number][]
  ).filter(([, count]) => count > 0)
})

const actionLabel = (action: Action) =>
  t(`inventory.import.action${imported.value ? 'Done' : ''}.${action}`)

const columns = computed<DataTableColumns<ResultRow>>(() => [
  { key: 'row', title: t('inventory.import.row'), width: 64 },
  {
    key: 'action',
    title: t('inventory.import.result'),
    width: 130,
    render: (row) =>
      h(NTag, { type: ACTION_TAGS[row.action], size: 'small', bordered: false }, () =>
        actionLabel(row.action),
      ),
  },
  {
    key: 'inventory_number',
    title: t('inventory.fields.inventoryNumber'),
    width: 140,
    render: (row) => row.inventory_number || '—',
  },
  {
    key: 'model',
    title: t('inventory.fields.model'),
    width: 180,
    render: (row) => row.model || '—',
  },
  {
    key: 'details',
    title: t('inventory.import.details'),
    render: (row) =>
      row.errors.length
        ? h(
            'ul',
            { class: 'messages' },
            row.errors.map((e) =>
              h(
                'li',
                h(NText, { type: 'error' }, () => e),
              ),
            ),
          )
        : h(
            'ul',
            { class: 'messages' },
            row.changes.map((c) =>
              h('li', [
                h('span', { class: 'muted' }, `${fieldLabel(c.field)}: `),
                c.old ? h('s', { class: 'muted' }, c.old) : null,
                c.old ? ' → ' : null,
                c.new || '—',
              ]),
            ),
          ),
  },
])
</script>

<template>
  <NModal
    v-model:show="show"
    preset="card"
    :title="t('inventory.import.title')"
    style="max-width: 1080px"
    :mask-closable="false"
  >
    <NSteps :current="step" size="small" class="steps">
      <NStep :title="t('inventory.import.stepFile')" />
      <NStep :title="t('inventory.import.stepMapping')" />
      <NStep :title="t('inventory.import.stepPreview')" />
    </NSteps>

    <!-- 1: file -->
    <div v-if="step === 1" class="stack">
      <p class="muted">{{ t('inventory.import.help') }}</p>
      <input
        ref="fileInput"
        type="file"
        accept=".csv,.txt,.xlsx,.xlsm,text/csv,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        class="file-input"
        :aria-label="t('inventory.import.pickFile')"
        data-test="import-file"
        @change="onFile"
      />
      <NButton size="large" dashed class="pick" @click="fileInput?.click()">
        <template #icon><FileUp :size="18" /></template>
        {{ t('inventory.import.pickFile') }}
      </NButton>
      <NAlert v-if="readError" type="error" :show-icon="false">{{ readError }}</NAlert>
    </div>

    <!-- 2: mapping -->
    <div v-else-if="step === 2 && table" class="stack">
      <p class="muted">
        {{
          t('inventory.import.fileInfo', {
            file: fileName,
            rows: table.rows.length,
            columns: table.headers.length,
          })
        }}
      </p>
      <div v-if="sheets.length > 1" class="sheet">
        <FieldLabel :label="t('inventory.import.sheet')" />
        <NSelect
          :value="sheetIndex"
          :options="sheetOptions"
          data-test="sheet"
          @update:value="selectSheet"
        />
      </div>
      <ToggleRow
        :model-value="hasHeader"
        :label="t('inventory.import.hasHeader')"
        :help="t('inventory.import.hasHeaderHelp')"
        data-test="has-header"
        @update:model-value="setHasHeader"
      />
      <div class="mapping">
        <div class="mapping-head muted">
          <span>{{ t('inventory.import.field') }}</span>
          <span>{{ t('inventory.import.sourceColumn') }}</span>
          <span>{{ t('inventory.import.sample') }}</span>
        </div>
        <div v-for="field in IMPORT_FIELDS" :key="field" class="mapping-row">
          <FieldLabel :label="fieldLabel(field)" :required="field === 'model' && modelMissing" />
          <NSelect
            v-model:value="mapping[field]"
            :options="columnOptions"
            :placeholder="t('inventory.import.notImported')"
            :data-test="`map-${field}`"
            filterable
            clearable
            size="small"
          />
          <span class="sample" :title="sampleValue(table.rows, mapping[field])">
            {{ sampleValue(table.rows, mapping[field]) }}
          </span>
        </div>
      </div>

      <h4 class="section">{{ t('inventory.import.newDevices') }}</h4>
      <p class="muted">{{ t('inventory.import.newDevicesHelp') }}</p>
      <div class="cols">
        <div>
          <FieldLabel :label="t('inventory.fields.model')" :required="modelMissing" />
          <EntitySelect
            v-model="defaults.model"
            :fetcher="assetModelsApi.list"
            :params="{ tracking: 'serialized' }"
            :label="modelLabel"
          />
        </div>
        <div>
          <FieldLabel :label="t('inventory.fields.location')" />
          <EntitySelect
            v-model="defaults.location"
            :fetcher="locationsApi.list"
            :label="(l) => l.full_name"
          />
        </div>
        <div>
          <FieldLabel :label="t('common.status')" />
          <NSelect
            v-model:value="defaults.status"
            :options="ASSET_STATUSES.map((s) => ({ value: s, label: enumLabel('assetStatus', s) }))"
            clearable
          />
        </div>
        <div>
          <FieldLabel :label="t('inventory.fields.condition')" />
          <NSelect
            v-model:value="defaults.condition"
            :options="ASSET_CONDITIONS.map((c) => ({ value: c, label: enumLabel('condition', c) }))"
            clearable
          />
        </div>
      </div>

      <h4 class="section">{{ t('inventory.import.existingDevices') }}</h4>
      <div class="cols">
        <div>
          <FieldLabel :label="t('inventory.import.matchBy')" />
          <NSelect v-model:value="matchBy" :options="matchOptions" data-test="match-by" />
        </div>
        <div v-if="matchBy !== NO_MATCH" class="span-3">
          <FieldLabel :label="t('inventory.import.whenFound')" />
          <NRadioGroup v-model:value="existing">
            <NRadioButton value="update">{{ t('inventory.import.update') }}</NRadioButton>
            <NRadioButton value="skip">{{ t('inventory.import.skip') }}</NRadioButton>
          </NRadioGroup>
        </div>
      </div>
      <ToggleRow
        v-if="matchBy !== NO_MATCH"
        v-model="ignoreCase"
        :label="t('inventory.import.ignoreCase')"
        :help="t('inventory.import.ignoreCaseHelp')"
        data-test="ignore-case"
      />
    </div>

    <!-- 3: preview / result -->
    <div v-else-if="step === 3 && result" class="stack">
      <NAlert :type="imported ? 'success' : 'info'" :show-icon="false">
        {{ imported ? t('inventory.import.doneHelp') : t('inventory.import.previewHelp') }}
      </NAlert>
      <div class="row summary">
        <NTag
          v-for="[action, count] in summary"
          :key="action"
          :type="ACTION_TAGS[action]"
          :bordered="false"
        >
          {{ actionLabel(action) }}: {{ count }}
        </NTag>
        <span class="spacer" />
        <NRadioGroup v-model:value="filter" size="small">
          <NRadioButton value="all">{{ t('inventory.import.filterAll') }}</NRadioButton>
          <NRadioButton value="changes">{{ t('inventory.import.filterChanges') }}</NRadioButton>
          <NRadioButton value="errors">{{ t('inventory.import.filterErrors') }}</NRadioButton>
        </NRadioGroup>
      </div>
      <NDataTable
        :columns="columns"
        :data="visibleRows"
        :row-key="(r: ResultRow) => r.row"
        :pagination="{ pageSize: 50 }"
        :max-height="420"
        size="small"
        data-test="import-preview"
      />
    </div>

    <template #footer>
      <div class="row" style="justify-content: flex-end">
        <template v-if="step === 1">
          <NButton @click="show = false">{{ t('common.cancel') }}</NButton>
        </template>
        <template v-else-if="step === 2">
          <NButton @click="reset">{{ t('inventory.import.otherFile') }}</NButton>
          <NButton
            type="primary"
            :disabled="!mappedCount"
            :loading="busy"
            data-test="import-preview-button"
            @click="preview"
          >
            {{ t('inventory.import.showPreview') }}
          </NButton>
        </template>
        <template v-else-if="imported">
          <NButton type="primary" @click="show = false">{{ t('common.close') }}</NButton>
        </template>
        <template v-else>
          <NButton @click="step = 2">{{ t('common.back') }}</NButton>
          <NButton
            type="primary"
            :disabled="!pending"
            :loading="busy"
            data-test="import-run"
            @click="runImport"
          >
            {{ t('inventory.import.run', { count: pending }) }}
          </NButton>
        </template>
      </div>
    </template>
  </NModal>
</template>

<style scoped>
.sheet {
  max-width: 320px;
}
.steps {
  margin-bottom: 20px;
}
.file-input {
  display: none;
}
.pick {
  height: 96px;
}
.mapping {
  display: grid;
  gap: 6px;
  max-height: 46vh;
  overflow: auto;
}
.mapping-head,
.mapping-row {
  display: grid;
  grid-template-columns: 200px minmax(0, 1fr) minmax(0, 1fr);
  gap: 12px;
  align-items: center;
}
.mapping-head {
  font-size: 12px;
}
.sample {
  font-family: var(--ar-font-mono);
  font-size: 12px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.section {
  margin: 8px 0 0;
}
.cols {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}
.span-3 {
  grid-column: span 3;
}
.summary {
  flex-wrap: wrap;
  gap: 8px;
}
.spacer {
  flex: 1;
}
:deep(.messages) {
  margin: 0;
  padding: 0;
  list-style: none;
  font-size: 12px;
}
@media (max-width: 720px) {
  .mapping-head,
  .mapping-row {
    grid-template-columns: 1fr;
  }
  .cols {
    grid-template-columns: 1fr;
  }
  .span-3 {
    grid-column: auto;
  }
}
</style>
