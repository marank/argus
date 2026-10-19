import { useDebounceFn } from '@vueuse/core'
import type { DataTableSortState, PaginationProps } from 'naive-ui'
import { computed, reactive, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { ListParams, Page } from '@/types/common'

/**
 * State for a server-side paginated, searchable and sortable list.
 *
 * Bind `pagination`, `onSort` and `rows` to an `NDataTable` with `remote`.
 */
export function useList<T>(
  fetcher: (params: ListParams) => Promise<Page<T>>,
  options: {
    filters?: Record<string, unknown>
    pageSize?: number
    ordering?: string
    /** Ordering applied before the user's sort, e.g. to keep rows grouped by category. */
    groupOrdering?: () => string | undefined
  } = {},
) {
  const { t } = useI18n()
  const rows = ref<T[]>([]) as { value: T[] }
  const count = ref(0)
  const loading = ref(false)
  const search = ref('')
  const ordering = ref(options.ordering ?? '')
  const filters = reactive<Record<string, unknown>>({ ...options.filters })
  const page = ref(1)
  const pageSize = ref(options.pageSize ?? 25)

  async function load() {
    loading.value = true
    try {
      const result = await fetcher({
        page: page.value,
        page_size: pageSize.value,
        q: search.value || undefined,
        ordering:
          [options.groupOrdering?.(), ordering.value].filter(Boolean).join(',') || undefined,
        ...(filters as ListParams),
      })
      rows.value = result.items
      count.value = result.count
    } finally {
      loading.value = false
    }
  }

  const reload = () => {
    page.value = 1
    return load()
  }
  const debouncedReload = useDebounceFn(reload, 250)

  watch(search, debouncedReload)
  watch(filters, reload, { deep: true })

  const pagination = computed<PaginationProps>(() => ({
    page: page.value,
    pageSize: pageSize.value,
    itemCount: count.value,
    pageSizes: [25, 50, 100],
    showSizePicker: true,
    prefix: () => t('common.records', { count: count.value }),
    onUpdatePage: (value: number) => {
      page.value = value
      load()
    },
    onUpdatePageSize: (value: number) => {
      pageSize.value = value
      reload()
    },
  }))

  function onSort(state: DataTableSortState | DataTableSortState[] | null) {
    const sorter = Array.isArray(state) ? state[0] : state
    if (!sorter || !sorter.order) ordering.value = options.ordering ?? ''
    else ordering.value = `${sorter.order === 'descend' ? '-' : ''}${String(sorter.columnKey)}`
    reload()
  }

  return { rows, count, loading, search, filters, ordering, pagination, load, reload, onSort }
}
