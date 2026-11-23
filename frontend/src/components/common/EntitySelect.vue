<script setup lang="ts" generic="T extends { id: Id }">
import { useDebounceFn } from '@vueuse/core'
import { NSelect, NTag, type SelectOption, type SelectRenderTag } from 'naive-ui'
import { computed, h, onMounted, ref, shallowReactive, watch } from 'vue'

import type { Id, ListParams, Page } from '@/types/common'

/**
 * Searchable select backed by a paginated API list endpoint.
 * Options are loaded on demand; the currently selected record is passed via `initial`
 * so its label shows without an extra request. `select` only hands out records loaded
 * from the list, never `initial`, which may be a reference with fewer fields.
 */
const props = withDefaults(
  defineProps<{
    fetcher: (params: ListParams) => Promise<Page<T>>
    label: (item: T) => string
    params?: ListParams
    initial?: T | T[] | null
    /** Items to list first (e.g. members of the chosen team); the order is kept otherwise. */
    prefer?: (item: T) => boolean
    multiple?: boolean
    placeholder?: string
    maxTagCount?: number | 'responsive'
    clearable?: boolean
    disabled?: boolean
    size?: 'small' | 'medium' | 'large'
  }>(),
  {
    params: undefined,
    initial: undefined,
    prefer: undefined,
    placeholder: undefined,
    maxTagCount: undefined,
    clearable: true,
    size: undefined,
  },
)

const model = defineModel<Id | Id[] | null>({ default: null })
const emit = defineEmits<{
  select: [item: T | null]
  /** Labels of the selected records, as far as they are known (e.g. for filter chips). */
  labels: [labels: string[]]
}>()

const items = ref<T[]>([]) as { value: T[] }
const loading = ref(false)
// The options load in the background on mount; the spinner only matters while the list is open.
const open = ref(false)
// Records loaded from the list; `select` only hands these out, as only they are complete.
const known = new Map<Id, T>()
// What `initial` named, for labels of selected records that were not loaded (yet).
// Reactive: `initial` may arrive after the value (a form prefilled once loaded), and the
// label must follow then instead of showing the bare id.
const initials = shallowReactive(new Map<Id, T>())

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
  const prefer = props.prefer
  const ordered = prefer
    ? [...list.filter((i) => prefer(i)), ...list.filter((i) => !prefer(i))]
    : list
  const result: SelectOption[] = ordered.map((item) => ({
    label: props.label(item),
    value: item.id,
  }))
  for (const id of selected) {
    if (result.some((o) => o.value === id)) continue
    const item = known.get(id) ?? initials.get(id)
    if (item) result.unshift({ label: props.label(item), value: id })
  }
  return result
})

watch(
  () => props.initial,
  (value) => {
    for (const item of Array.isArray(value) ? value : value ? [value] : [])
      initials.set(item.id, item)
  },
  { immediate: true },
)
watch(
  () => JSON.stringify(props.params),
  () => load(),
)
onMounted(() => load())

watch(
  [model, options],
  () => {
    const selected = Array.isArray(model.value) ? model.value : model.value ? [model.value] : []
    emit(
      'labels',
      selected.flatMap((id) => {
        const option = options.value.find((o) => o.value === id)
        return option ? [String(option.label)] : []
      }),
    )
  },
  { immediate: true },
)

/** Selected items of a multiple select as soft, round chips instead of bordered boxes. */
const renderTag: SelectRenderTag = ({ option, handleClose }) =>
  h(
    NTag,
    {
      class: 'entity-tag',
      size: 'small',
      round: true,
      bordered: false,
      closable: !props.disabled,
      color: { color: 'var(--ar-primary-soft)', textColor: 'var(--ar-primary)' },
      onClose: (e: MouseEvent) => {
        e.stopPropagation()
        handleClose()
      },
    },
    { default: () => option.label as string },
  )

function onUpdate(value: Id | Id[] | null) {
  model.value = value
  if (!Array.isArray(value)) emit('select', value ? (known.get(value) ?? null) : null)
}
</script>

<template>
  <NSelect
    :value="model"
    :options="options"
    :loading="loading && open"
    :multiple="multiple"
    :placeholder="placeholder"
    :max-tag-count="maxTagCount"
    :clearable="clearable"
    :disabled="disabled"
    :size="size"
    :render-tag="multiple ? renderTag : undefined"
    filterable
    remote
    @search="onSearch"
    @update:value="onUpdate"
    @update:show="(value: boolean) => (open = value)"
  />
</template>
