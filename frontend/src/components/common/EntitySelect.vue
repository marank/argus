<script setup lang="ts" generic="T extends { id: Id }">
import { useDebounceFn } from '@vueuse/core'
import { NSelect, type SelectOption } from 'naive-ui'
import { computed, onMounted, ref, watch } from 'vue'

import type { Id, ListParams, Page } from '@/types/common'

/**
 * Searchable select backed by a paginated API list endpoint.
 * Options are loaded on demand; the currently selected record is passed via `initial`
 * so its label shows without an extra request.
 */
const props = withDefaults(
  defineProps<{
    fetcher: (params: ListParams) => Promise<Page<T>>
    label: (item: T) => string
    params?: ListParams
    initial?: T | T[] | null
    multiple?: boolean
    placeholder?: string
    clearable?: boolean
    disabled?: boolean
    size?: 'small' | 'medium' | 'large'
  }>(),
  { clearable: true, size: undefined },
)

const model = defineModel<Id | Id[] | null>({ default: null })
const emit = defineEmits<{ select: [item: T | null] }>()

const items = ref<T[]>([]) as { value: T[] }
const loading = ref(false)
const known = new Map<Id, T>()

function remember(list: T[]) {
  for (const item of list) known.set(item.id, item)
}

async function load(q = '') {
  loading.value = true
  try {
    const page = await props.fetcher({ ...props.params, q: q || undefined, page_size: 30 })
    remember(page.items)
    items.value = page.items
  } finally {
    loading.value = false
  }
}

const onSearch = useDebounceFn((q: string) => load(q), 200)

const options = computed<SelectOption[]>(() => {
  const list = [...items.value]
  const selected = Array.isArray(model.value) ? model.value : model.value ? [model.value] : []
  for (const id of selected) {
    const item = known.get(id)
    if (item && !list.some((i) => i.id === id)) list.unshift(item)
  }
  return list.map((item) => ({ label: props.label(item), value: item.id }))
})

watch(
  () => props.initial,
  (value) => remember(Array.isArray(value) ? value : value ? [value] : []),
  { immediate: true },
)
watch(
  () => JSON.stringify(props.params),
  () => load(),
)
onMounted(() => load())

function onUpdate(value: Id | Id[] | null) {
  model.value = value
  if (!Array.isArray(value)) emit('select', value ? (known.get(value) ?? null) : null)
}
</script>

<template>
  <NSelect
    :value="model"
    :options="options"
    :loading="loading"
    :multiple="multiple"
    :placeholder="placeholder"
    :clearable="clearable"
    :disabled="disabled"
    :size="size"
    filterable
    remote
    @search="onSearch"
    @update:value="onUpdate"
  />
</template>
