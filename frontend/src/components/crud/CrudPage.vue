<script setup lang="ts">
import { Pencil, Plus, Trash2 } from '@lucide/vue'
import { NButton, NDataTable, NInput, NSelect, type DataTableColumns } from 'naive-ui'
import { computed, h, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import EntitySelect from '@/components/common/EntitySelect.vue'
import PageHeader from '@/components/common/PageHeader.vue'
import { useAction } from '@/composables/useAction'
import { useConfirm } from '@/composables/useConfirm'
import { useFormat } from '@/composables/useFormat'
import { useList } from '@/composables/useList'

import CrudFormDrawer from './CrudFormDrawer.vue'
import type { ResourceDef } from './types'

/* eslint-disable @typescript-eslint/no-explicit-any */
const props = defineProps<{ resource: ResourceDef<any> }>()
const { t } = useI18n()
const confirm = useConfirm()
const { enumLabel } = useFormat()
const { run } = useAction()

const list = useList(props.resource.api.list, {
  ordering: props.resource.ordering,
  filters: Object.fromEntries((props.resource.filters ?? []).map((f) => [f.key, null])),
})
onMounted(list.load)

const editing = ref<any | null>(null)
const showForm = ref(false)

function edit(row: any | null) {
  editing.value = row
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

const columns = computed<DataTableColumns<any>>(() => [
  ...props.resource.columns.map((column) => ({
    key: column.sorter ?? column.key,
    title: t(column.label),
    sorter: column.sorter ? true : undefined,
    width: column.width,
    ellipsis: { tooltip: true },
    render: column.render ?? ((row: any) => row[column.key] ?? '—'),
  })),
  {
    key: '_actions',
    title: '',
    width: 84,
    align: 'right' as const,
    render: (row: any) =>
      h('div', { class: 'row row-actions', style: 'justify-content:flex-end' }, [
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
        h(
          NButton,
          {
            quaternary: true,
            size: 'tiny',
            type: 'error',
            title: t('common.delete'),
            onClick: (e: Event) => (e.stopPropagation(), remove(row)),
          },
          { icon: () => h(Trash2, { size: 13 }) },
        ),
      ]),
  },
])

const boolOptions = computed(() => [
  { value: 'true', label: t('common.yes') },
  { value: 'false', label: t('common.no') },
])
</script>

<template>
  <div class="page">
    <PageHeader :title="t(`masterdata.resources.${resource.key}`)" :eyebrow="t('masterdata.title')">
      <template #actions>
        <NButton type="primary" @click="edit(null)">
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
      </div>
      <NDataTable
        class="clickable-rows"
        remote
        size="small"
        :columns="columns"
        :data="list.rows.value"
        :loading="list.loading.value"
        :pagination="list.pagination.value"
        :row-key="(row: any) => row.id"
        :row-props="(row: any) => ({ onClick: () => edit(row) })"
        :scroll-x="900"
        @update:sorter="list.onSort"
      />
    </div>
    <CrudFormDrawer
      v-model:show="showForm"
      :resource="resource"
      :row="editing"
      @saved="list.load"
    />
  </div>
</template>

<style scoped>
:deep(.cell-yes) {
  color: var(--ar-success);
}
</style>
