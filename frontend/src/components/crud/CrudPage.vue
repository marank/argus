<script setup lang="ts">
import { Pencil, Plus, Trash2 } from '@lucide/vue'
import { useStorage } from '@vueuse/core'
import { NButton } from 'naive-ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import CheckField from '@/components/common/CheckField.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import ListTable from '@/components/table/ListTable.vue'
import TableToolbar from '@/components/table/TableToolbar.vue'
import type { TableColumn, TableFilter, TableGrouping } from '@/components/table/types'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'
import { useTableView } from '@/composables/useTableView'
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
  if ((await run(() => props.resource.api.remove(row.id))) !== undefined) list.load()
}

const filters = computed<TableFilter[]>(() =>
  (props.resource.filters ?? []).map((filter): TableFilter => {
    const base = { key: filter.key, label: t(filter.label) }
    if (filter.type === 'boolean') return { ...base, type: 'boolean' }
    if (filter.type === 'enum')
      return {
        ...base,
        type: 'select',
        options: (filter.values ?? []).map((v) => ({
          value: v,
          label: enumLabel(filter.group!, v),
        })),
      }
    return { ...base, type: 'entity', fetcher: filter.fetcher!, display: filter.display! }
  }),
)

const groupings = (): TableGrouping<any>[] =>
  (props.resource.groupings ?? []).map((g) => ({ ...g, label: t(g.label) }))

const columns = computed<TableColumn<any>[]>(() => [
  ...props.resource.columns.filter(isVisible).map((column, index): TableColumn<any> => {
    const render = column.render ?? ((row: any) => row[column.key] ?? '—')
    const treeColumn = treeActive.value && index === 0
    return {
      key: column.sorter ?? column.key,
      title: t(column.label),
      sorter: column.sorter && !treeActive.value ? true : undefined,
      // The first column names the record; the tree view indents it.
      hideable: index === 0 ? false : undefined,
      hidden: column.hidden,
      width: column.width,
      // Columns without a fixed width share the rest but never collapse.
      minWidth: column.width ? undefined : 180,
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

const view = useTableView<any>({
  id: props.resource.key,
  columns: () => columns.value,
  rows: (): any[] => list.rows.value,
  groupings,
  defaultGrouping: props.resource.groupings?.[0]?.key,
  visible: (row): boolean => tree.isShown(row),
  rowClass: (row): string => tree.rowClass(row),
})

const list = useList(props.resource.api.list, {
  ordering: props.resource.ordering,
  // The tree keeps each record below its parent (within its group); column sorting is off.
  groupOrdering: (): string | undefined =>
    [view.groupOrdering(), treeActive.value ? props.resource.tree?.ordering : null]
      .filter(Boolean)
      .join(',') || undefined,
  filters: Object.fromEntries(
    (props.resource.filters ?? []).map((f) => [f.key, f.type === 'boolean' ? null : []]),
  ),
})
onMounted(list.load)
// Before the reload that the new group ordering starts: drop the column sort.
watch(treeActive, () => (list.ordering.value = props.resource.ordering ?? ''), { flush: 'sync' })

const tree = useTreeRows<any>({
  rows: (): any[] => list.rows.value,
  parent: (row) => props.resource.tree!.parent(row),
  group: (row): string => view.grouping.value?.rowKey(row) ?? '',
  enabled: () => treeActive.value,
  // While searching, every hit shows.
  collapsible: () => !list.search.value,
  storageKey: `argus.tree.collapsed.${props.resource.key}`,
})
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
      <TableToolbar v-model:search="list.search.value" :list="list" :filters="filters" :view="view">
        <CheckField v-if="resource.tree" v-model="treeView" :label="t('masterdata.treeView')" />
      </TableToolbar>
      <!-- Rebuilt on switching the tree view, which drops the sort state of the headers. -->
      <ListTable :key="String(treeActive)" :view="view" :list="list" @row-click="edit" />
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
