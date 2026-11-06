<script setup lang="ts">
import { Group, ListFilter, Plus, X } from '@lucide/vue'
import { NButton, NInput, NPopselect, NSelect, NTag, type SelectOption } from 'naive-ui'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import EntitySelect from '@/components/common/EntitySelect.vue'
import type { TableView } from '@/composables/useTableView'
import type { Id } from '@/types/common'
import { formatDateRange, type DateRange } from '@/utils/dateRange'

import ColumnSettings from './ColumnSettings.vue'
import DateRangeInput from './DateRangeInput.vue'
import type { TableFilter } from './types'

/* eslint-disable @typescript-eslint/no-explicit-any */

type SelectValue = string | string[] | null
type EntityValue = Id | Id[] | null

/**
 * The toolbar above a list table: the search field, a filter panel that opens below it,
 * the grouping menu and the column settings. The panel holds one condition per line:
 * a field (one of the table's filters) and its value; all of them must match. While the
 * panel is closed, the active filters show as chips below the toolbar.
 * `prefix` holds controls before the search (e.g. scope tabs), the default slot more after it.
 */
const props = defineProps<{
  /** The list (`useList`) whose filters the panel shows and changes. */
  list: { filters: Record<string, unknown>; setFilter: (key: string, value: unknown) => void }
  filters?: TableFilter[]
  view?: TableView<any>
}>()
const search = defineModel<string>('search', { required: true })
const { t, locale } = useI18n()

const isSet = (value: unknown) =>
  Array.isArray(value) ? value.length > 0 : value !== null && value !== undefined && value !== ''

const open = ref(false)
const byKey = computed(() => new Map((props.filters ?? []).map((f) => [f.key, f])))
/** The list filters a field sets: both ends of a date range, the own key otherwise. */
const listKeys = (filter: TableFilter) =>
  filter.type === 'daterange' ? [filter.from, filter.until] : [filter.key]
const isActive = (filter: TableFilter) => listKeys(filter).some((k) => isSet(props.list.filters[k]))
const active = computed(() => (props.filters ?? []).filter(isActive))

/**
 * The rule lines of the panel, by filter key; null for a line whose field is not chosen
 * yet. Every active filter has a line; lines without a value yet stay until removed.
 */
const rows = ref<(string | null)[]>([])
watch(
  () => active.value.map((f) => f.key),
  (keys) => {
    for (const key of keys) if (!rows.value.includes(key)) rows.value.push(key)
  },
  { immediate: true },
)

function toggleOpen() {
  open.value = !open.value
  // An empty panel starts with a line to fill in.
  if (open.value && !rows.value.length) rows.value.push(null)
}

/** Fields not used by another line, alphabetically. */
function fieldOptions(own: string | null): SelectOption[] {
  return (props.filters ?? [])
    .filter((f) => f.key === own || !rows.value.includes(f.key))
    .map((f) => ({ value: f.key, label: f.label }))
    .sort((a, b) => a.label.localeCompare(b.label, locale.value))
}

function setField(index: number, key: string) {
  const old = rows.value[index]
  if (old) clear(old)
  rows.value[index] = key
  const filter = byKey.value.get(key)
  // A switch has no value to choose: picking it turns it on.
  if (filter?.type === 'toggle') props.list.setFilter(key, filter.on())
}

function removeRow(index: number) {
  const key = rows.value[index]
  if (key) clear(key)
  rows.value.splice(index, 1)
}

/** Labels of the records chosen in entity filters, reported by their selects. */
const entityLabels = reactive<Record<string, string[]>>({})

function chipValue(filter: TableFilter): string {
  const value = props.list.filters[filter.key]
  const values = (Array.isArray(value) ? value : [value]).map(String)
  switch (filter.type) {
    case 'select':
      return values.map((v) => filter.options.find((o) => o.value === v)?.label ?? v).join(', ')
    case 'entity':
      return (entityLabels[filter.key] ?? []).join(', ')
    case 'boolean':
      return values[0] === 'true' ? t('common.yes') : t('common.no')
    case 'daterange':
      return formatDateRange(rangeOf(filter))
    case 'toggle':
      return ''
  }
}

function clear(key: string) {
  const filter = byKey.value.get(key)
  for (const k of filter ? listKeys(filter) : [key])
    props.list.setFilter(k, Array.isArray(props.list.filters[k]) ? [] : null)
}

function clearChip(key: string) {
  clear(key)
  rows.value = rows.value.filter((k) => k !== key)
}

function clearAll() {
  for (const filter of active.value) clear(filter.key)
  rows.value = []
}

const boolOptions = computed(() => [
  { value: 'true', label: t('common.yes') },
  { value: 'false', label: t('common.no') },
])

function rangeOf(filter: TableFilter & { type: 'daterange' }): DateRange {
  const value = (k: string) => (props.list.filters[k] as string | null | undefined) || null
  return { from: value(filter.from), until: value(filter.until) }
}

function setRange(filter: TableFilter & { type: 'daterange' }, range: DateRange) {
  props.list.setFilter(filter.from, range.from)
  props.list.setFilter(filter.until, range.until)
}

const NONE = '__none'
/** "No grouping" first, then the groupings alphabetically. */
const groupOptions = computed(() => [
  { value: NONE, label: t('table.noGrouping') },
  ...(props.view?.groupings.value ?? [])
    .map((g) => ({ value: g.key, label: g.label }))
    .sort((a, b) => a.label.localeCompare(b.label, locale.value)),
])
</script>

<template>
  <div class="table-toolbar">
    <div class="toolbar">
      <slot name="prefix" />
      <NInput v-model:value="search" class="grow" :placeholder="t('common.search')" clearable />
      <NButton
        v-if="filters?.length"
        :type="open ? 'primary' : 'default'"
        :secondary="open"
        :aria-expanded="open"
        @click="toggleOpen"
      >
        <template #icon><ListFilter :size="16" /></template>
        {{ t('common.filters') }}
        <span v-if="active.length" class="filter-count mono">{{ active.length }}</span>
      </NButton>
      <NPopselect
        v-if="view && view.groupings.value.length"
        :value="view.grouping.value?.key ?? NONE"
        :options="groupOptions"
        trigger="click"
        @update:value="(key: string) => view!.setGrouping(key === NONE ? null : key)"
      >
        <NButton :title="t('table.grouping')">
          <template #icon><Group :size="16" /></template>
          {{ view.grouping.value?.label ?? t('table.grouping') }}
        </NButton>
      </NPopselect>
      <ColumnSettings v-if="view" :view="view" />
      <slot />
    </div>

    <div v-if="filters?.length" v-show="open" class="filter-panel">
      <div class="panel-head">
        <span class="panel-title">{{ t('common.filters') }}</span>
        <NButton v-if="active.length" text size="tiny" class="clear-all" @click="clearAll">
          {{ t('table.clearFilters') }}
        </NButton>
      </div>
      <div class="rules">
        <div
          v-for="(key, index) in rows"
          :key="key ?? `new-${index}`"
          :class="['rule', { set: !!key && !!byKey.get(key) && isActive(byKey.get(key)!) }]"
          :data-filter="key ?? undefined"
        >
          <NSelect
            class="rule-field"
            size="small"
            :value="key"
            :options="fieldOptions(key)"
            :placeholder="t('table.chooseField')"
            filterable
            @update:value="(k: string) => setField(index, k)"
          />
          <span class="rule-op">{{ t('table.is') }}</span>
          <div class="rule-value">
            <template v-if="key && byKey.get(key)">
              <NSelect
                v-if="byKey.get(key)!.type === 'select'"
                size="small"
                :value="list.filters[key] as SelectValue"
                :options="
                  (byKey.get(key) as TableFilter & { type: 'select' }).options as SelectOption[]
                "
                multiple
                max-tag-count="responsive"
                :placeholder="t('table.enterValue')"
                clearable
                @update:value="(v: SelectValue) => list.setFilter(key, v)"
              />
              <NSelect
                v-else-if="byKey.get(key)!.type === 'boolean'"
                size="small"
                :value="list.filters[key] as SelectValue"
                :options="boolOptions"
                :placeholder="t('table.enterValue')"
                clearable
                @update:value="(v: SelectValue) => list.setFilter(key, v)"
              />
              <DateRangeInput
                v-else-if="byKey.get(key)!.type === 'daterange'"
                size="small"
                :value="rangeOf(byKey.get(key) as TableFilter & { type: 'daterange' })"
                @update:value="
                  (r: DateRange) =>
                    setRange(byKey.get(key) as TableFilter & { type: 'daterange' }, r)
                "
              />
              <EntitySelect
                v-else-if="byKey.get(key)!.type === 'entity'"
                size="small"
                :model-value="list.filters[key] as EntityValue"
                :fetcher="(byKey.get(key) as TableFilter & { type: 'entity' }).fetcher"
                :label="(byKey.get(key) as TableFilter & { type: 'entity' }).display"
                :params="(byKey.get(key) as TableFilter & { type: 'entity' }).params"
                multiple
                max-tag-count="responsive"
                :placeholder="t('table.enterValue')"
                @update:model-value="(v: EntityValue) => list.setFilter(key, v)"
                @labels="(labels: string[]) => (entityLabels[key] = labels)"
              />
              <span v-else class="rule-fixed">{{ t('common.yes') }}</span>
            </template>
            <span v-else class="rule-hint">{{ t('table.enterValue') }}</span>
          </div>
          <button
            type="button"
            class="rule-remove"
            :title="t('table.removeFilter')"
            :aria-label="t('table.removeFilter')"
            @click="removeRow(index)"
          >
            <X :size="14" />
          </button>
        </div>
        <div class="rule-add">
          <NButton
            text
            size="small"
            type="primary"
            :disabled="rows.length >= (filters?.length ?? 0) || rows.includes(null)"
            @click="rows.push(null)"
          >
            <template #icon><Plus :size="14" /></template>
            {{ t('table.addCondition') }}
          </NButton>
        </div>
      </div>
    </div>

    <!-- While the panel is open it shows the filters itself. -->
    <div v-if="active.length && !open" class="filter-chips">
      <NTag
        v-for="filter in active"
        :key="filter.key"
        size="small"
        round
        closable
        :bordered="false"
        :color="{ color: 'var(--ar-primary-soft)', textColor: 'var(--ar-primary)' }"
        @close="clearChip(filter.key)"
      >
        <span class="chip-label">{{ filter.label }}</span>
        <template v-if="chipValue(filter)">: {{ chipValue(filter) }}</template>
      </NTag>
      <NButton text size="tiny" class="clear-all" @click="clearAll">
        <template #icon><X :size="12" /></template>
        {{ t('table.clearFilters') }}
      </NButton>
    </div>
  </div>
</template>

<style scoped>
.table-toolbar {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.filter-count {
  margin-left: 6px;
  padding: 0 5px;
  border-radius: 2px;
  background: var(--ar-primary);
  color: var(--ar-on-primary);
  font-size: 11px;
  line-height: 16px;
}
.filter-panel {
  padding: 10px 12px 12px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.panel-title {
  color: var(--ar-text-subtle);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}
/* The conditions hang on a line with a dot per condition, like the tree lines of the tables. */
.rules {
  position: relative;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-left: 22px;
}
.rules::before {
  content: '';
  position: absolute;
  top: 13px;
  bottom: 13px;
  left: 7px;
  border-left: 1px solid var(--ar-border-strong);
}
.rule,
.rule-add {
  position: relative;
}
.rule::before,
.rule-add::before {
  content: '';
  position: absolute;
  top: 50%;
  left: -19px;
  width: 9px;
  height: 9px;
  margin-top: -4.5px;
  border: 1px solid var(--ar-border-strong);
  border-radius: 50%;
  background: var(--ar-surface);
}
.rule.set::before {
  border-color: var(--ar-primary);
  background: var(--ar-primary);
}
.rule {
  display: grid;
  grid-template-columns: 200px 34px minmax(200px, 360px) 24px;
  justify-content: start;
  align-items: center;
  gap: 8px;
}
.rule-op {
  color: var(--ar-text-subtle);
  font-family: var(--ar-font-mono);
  font-size: 11px;
  text-transform: uppercase;
  white-space: nowrap;
}
.rule-value {
  min-width: 0;
}
.rule-hint {
  color: var(--ar-text-subtle);
  font-size: 12px;
}
.rule-fixed {
  font-size: 13px;
}
.rule-remove {
  display: inline-flex;
  padding: 3px;
  border: 0;
  border-radius: 2px;
  background: none;
  color: var(--ar-text-subtle);
  cursor: pointer;
}
.rule-remove:hover,
.rule-remove:focus-visible {
  color: var(--ar-error);
}
.rule-add {
  display: flex;
  align-items: center;
  min-height: 26px;
}
.filter-chips {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
.chip-label {
  font-weight: 600;
}
.clear-all {
  margin-left: 4px;
  color: var(--ar-text-muted);
}
@media (max-width: 640px) {
  .rule {
    grid-template-columns: 1fr 34px 24px;
  }
  .rule-value {
    grid-column: 1 / 3;
  }
}
</style>
