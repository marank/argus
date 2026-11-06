<script setup lang="ts" generic="T extends { id: Id }">
import { NDataTable, type DataTableSortState, type PaginationProps } from 'naive-ui'

import type { GroupRow } from '@/composables/useGroupedRows'
import type { TableView } from '@/composables/useTableView'
import type { Id } from '@/types/common'

/**
 * A server-paginated list table (`useList`) in the user's view (`useTableView`): their
 * columns, widths, grouping and density. Rows open with `onRowClick`, if given.
 */
defineProps<{
  view: TableView<T>
  list: {
    loading: { value: boolean }
    pagination: { value: PaginationProps }
    onSort: (state: DataTableSortState | DataTableSortState[] | null) => void
  }
  onRowClick?: (row: T) => void
}>()
</script>

<template>
  <NDataTable
    :class="{ 'clickable-rows': !!onRowClick }"
    remote
    :size="view.density.value"
    :columns="view.columns.value"
    :data="view.rows.value"
    :loading="list.loading.value"
    :pagination="list.pagination.value"
    :row-key="(row: T | GroupRow) => row.id"
    :row-props="(row: T | GroupRow) => view.rowProps(row, onRowClick)"
    :row-class-name="view.rowClass"
    :scroll-x="view.scrollX.value"
    @update:sorter="list.onSort"
    @unstable-column-resize="view.onResize"
  />
</template>
