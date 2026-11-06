<script setup lang="ts">
import { Pencil, Plus, Trash2 } from '@lucide/vue'
import { useStorage } from '@vueuse/core'
import { NButton, NDataTable, NInput, NSelect, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import CheckField from '@/components/common/CheckField.vue'
import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import { isGroupRow, useGroupedRows, withGroupHeaders } from '@/composables/useGroupedRows'
import { useList } from '@/composables/useList'
import { useTreeRows } from '@/composables/useTreeRows'
import { useAuthStore } from '@/stores/auth'

import CrudFormDrawer from './CrudFormDrawer.vue'
import { isVisible, type ResourceDef } from './types'

/* eslint-disable @typescript-eslint/no-explicit-any */
const props = defineProps<{ resource: ResourceDef<any> }>()
const auth = useAuthStore()
/** Without the right to write, records open for viewing only. */
const readonly = computed(() =>
  props.resource.superuser
    ? !auth.isSuperuser
    : !!props.resource.permission && !auth.can(props.resource.permission, 'write'),
)
const { t } = useI18n()
const confirm = useConfirm()
const { enumLabel } = useFormat()
const { run } = useAction()

/** Tree view, where the resource offers one; remembered per table. */
const treeView = useStorage(`argus.tree.${props.resource.key}`, true)
const treeActive = computed(() => !!props.resource.tree && treeView.value)

const list = useList(props.resource.api.list, {
  ordering: props.resource.ordering,
  // The tree keeps each record below its parent (within its group); column sorting is off.
  groupOrdering: () =>
    [props.resource.groupBy?.ordering, treeActive.value ? props.resource.tree?.ordering : null]
      .filter(Boolean)
      .join(',') || undefined,
  filters: Object.fromEntries((props.resource.filters ?? []).map((f) => [f.key, null])),
})
onMounted(list.load)
watch(treeActive, () => {
  list.ordering.value = props.resource.ordering ?? ''
  list.reload()
})

const editing = ref<any | null>(null)
/** A new record builds on this one (see `derive` of the resource). */
const source = ref<any | null>(null)
const showForm = ref(false)

function edit(row: any | null) {
  editing.value = row
  source.value = null
  showForm.value = true
}

function derive(row: any) {
  editing.value = null
  source.value = row
  showForm.value = true
}

async function remove(row: any) {
  if (
    !(await confirm(`${props.resource.title(row)}: ${t('common.confirmDelete')}`, { danger: true }))
  )
    return
  if ((await run(() => props.resource.api.remove(row.id), t('common.deleted'))) !== undefined)
    list.load()
}

const FLEX_MIN_WIDTH = 180

const tree = useTreeRows<any>({
  rows: () => list.rows.value,
  parent: (row) => props.resource.tree!.parent(row),
  group: props.resource.groupBy ? (row) => props.resource.groupBy!.key(row) : undefined,
  enabled: () => treeActive.value,
  // While searching, every hit shows.
  collapsible: () => !list.search.value,
  storageKey: `argus.tree.collapsed.${props.resource.key}`,
})

const baseColumns = computed<DataTableColumns<any>>(() => [
  ...props.resource.columns.filter(isVisible).map((column, index) => {
    const render = column.render ?? ((row: any) => row[column.key] ?? '—')
    const treeColumn = treeActive.value && index === 0
    return {
      key: column.sorter ?? column.key,
      title: t(column.label),
      sorter: column.sorter && !treeActive.value ? true : undefined,
      width: column.width,
      // Columns without a fixed width share the rest but never collapse.
      minWidth: column.width ? undefined : FLEX_MIN_WIDTH,
      // The tree cell cuts its text itself; a tooltip would repeat the tree lines.
      ellipsis: treeColumn ? false : { tooltip: true },
      className: treeColumn ? 'tree-cell' : undefined,
      render: treeColumn
        ? (row: any) =>
            tree.cell(row, tree.depth(row) ? props.resource.tree!.label(row) : render(row))
        : render,
    }
  }),
  {
    key: '_actions',
    title: '',
    width: readonly.value ? 0 : props.resource.derive ? 112 : 84,
    align: 'right' as const,
    render: (row: any) =>
      readonly.value
        ? null
        : h('div', { class: 'row row-actions', style: 'justify-content:flex-end' }, [
            props.resource.derive
              ? h(
                  NButton,
                  {
                    quaternary: true,
                    size: 'tiny',
                    title: t(props.resource.derive.label),
                    'aria-label': t(props.resource.derive.label),
                    onClick: (e: Event) => (e.stopPropagation(), derive(row)),
                  },
                  { icon: () => h(props.resource.derive!.icon, { size: 13 }) },
                )
              : null,
            h(
              NButton,
              {
                quaternary: true,
                size: 'tiny',
                title: t('common.edit'),
                onClick: (e: Event) => (e.stopPropagation(), edit(row)),
              },
              { icon: () => h(Pencil, { size: 13 }) },
            ),
            (props.resource.deletable?.(row) ?? true)
              ? h(
                  NButton,
                  {
                    quaternary: true,
                    size: 'tiny',
                    type: 'error',
                    title: t('common.delete'),
                    onClick: (e: Event) => (e.stopPropagation(), remove(row)),
                  },
                  { icon: () => h(Trash2, { size: 13 }) },
                )
              : null,
          ]),
  },
])

/** Wide enough for every column; narrower screens scroll the table sideways. */
const scrollX = computed(() =>
  baseColumns.value.reduce(
    (sum, column) => sum + Number(('width' in column && column.width) || FLEX_MIN_WIDTH),
    0,
  ),
)

const columns = computed(() =>
  props.resource.groupBy ? withGroupHeaders(baseColumns.value) : baseColumns.value,
)
const grouping = useGroupedRows<any>({
  rows: () => list.rows.value,
  key: (row) => props.resource.groupBy!.key(row),
  label: (row) => props.resource.groupBy!.label(row),
  enabled: () => !!props.resource.groupBy,
  visible: (row) => tree.isShown(row),
  storageKey: `argus.groups.${props.resource.key}`,
})

const rowClass = (row: any) =>
  [grouping.rowClass(row), isGroupRow(row) ? '' : tree.rowClass(row)].filter(Boolean).join(' ')

const boolOptions = computed(() => [
  { value: 'true', label: t('common.yes') },
  { value: 'false', label: t('common.no') },
])
</script>

<template>
  <div class="page">
    <PageHeader :title="t(`masterdata.resources.${resource.key}`)" :eyebrow="t('masterdata.title')">
      <template #actions>
        <NButton v-if="!readonly" type="primary" @click="edit(null)">
          <template #icon><Plus :size="16" /></template>
          {{ t(`masterdata.singular.${resource.key}`) }}
        </NButton>
      </template>
    </PageHeader>
    <div class="stack">
      <div class="toolbar">
        <NInput
          v-model:value="list.search.value"
          class="grow"
          :placeholder="t('common.search')"
          clearable
        />
        <template v-for="filter in resource.filters ?? []" :key="filter.key">
          <NSelect
            v-if="filter.type === 'boolean'"
            v-model:value="list.filters[filter.key] as string | null"
            :options="boolOptions"
            :placeholder="t(filter.label)"
            clearable
            style="width: 170px"
          />
          <NSelect
            v-else-if="filter.type === 'enum'"
            v-model:value="list.filters[filter.key] as string | null"
            :options="
              (filter.values ?? []).map((v) => ({ value: v, label: enumLabel(filter.group!, v) }))
            "
            :placeholder="t(filter.label)"
            clearable
            style="width: 170px"
          />
          <EntitySelect
            v-else
            v-model="list.filters[filter.key] as string | null"
            :fetcher="filter.fetcher!"
            :label="filter.display!"
            :placeholder="t(filter.label)"
            style="width: 200px"
          />
        </template>
        <CheckField v-if="resource.tree" v-model="treeView" :label="t('masterdata.treeView')" />
      </div>
      <!-- Rebuilt on switching the tree view, which drops the sort state of the headers. -->
      <NDataTable
        :key="String(treeActive)"
        class="clickable-rows"
        remote
        size="small"
        :columns="columns"
        :data="grouping.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(row: any) => row.id"
        :row-props="(row: any) => grouping.rowProps(row, edit)"
        :row-class-name="rowClass"
        :scroll-x="scrollX"
        @update:sorter="list.onSort"
      />
    </div>
    <CrudFormDrawer
      v-model:show="showForm"
      :resource="resource"
      :row="editing"
      :source="source"
      :readonly="readonly"
      @saved="list.load"
    />
  </div>
</template>

<style scoped>
:deep(.cell-yes) {
  color: var(--ar-success);
}
</style>
