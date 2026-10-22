<script setup lang="ts">
import { MessageSquarePlus, Search } from '@lucide/vue'
import { NInput } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import EmptyState from '@/components/common/EmptyState.vue'
import type { Id } from '@/types/common'
import type { CatalogCategory, CatalogModel } from '@/types/requests'
import { categoryIcon } from '@/utils/icons'
import { anyModelLabel } from '@/utils/requests'

import CatalogOptionRow from './CatalogOptionRow.vue'
import CategoryOptions from './CategoryOptions.vue'
import CustomRequestCard from './CustomRequestCard.vue'
import { offersAnyModel, optionKey, optionCounts, type CatalogOption } from './types'

/**
 * Catalog with search on top, below in two columns: all groups as a list on the
 * left, the selected group's options (or the search results) next to it. Accessory groups appear inside their
 * parent group. The default slot sits above the options (e.g. the quick pick).
 * For a direct hand-out (`direct`) the `direct` slot replaces search and options;
 * the groups on the left then browse what is in stock.
 */
const props = defineProps<{
  catalog: CatalogCategory[]
  cartCounts: Record<string, number>
  direct?: boolean
}>()
const emit = defineEmits<{
  add: [category: CatalogCategory, model?: CatalogModel]
  addFreeText: [text: string, category?: CatalogCategory]
}>()
const { t } = useI18n()

const query = ref('')
const topLevel = computed(() => {
  const ids = new Set(props.catalog.map((c) => c.id))
  return props.catalog.filter((c) => !c.parent_id || !ids.has(c.parent_id))
})
const childrenOf = (id: Id) => props.catalog.filter((c) => c.parent_id === id)
/** Tiles split into hardware and software, followed by the section for anything else. */
const tileGroups = computed(() =>
  (['hardware', 'software'] as const)
    // Direct hand-outs are for devices and consumables, not license seats.
    .filter((kind) => !props.direct || kind === 'hardware')
    .map((kind) => ({ kind, items: topLevel.value.filter((c) => c.kind === kind) }))
    .filter((group) => group.items.length),
)

/** Pseudo selection for the "something else" tile. */
const OTHER = 'other'
const selectedId = ref<Id | null>(null)
watch(
  topLevel,
  (groups) => {
    if (!selectedId.value && groups.length) selectedId.value = groups[0]!.id
  },
  { immediate: true },
)
const selected = computed(() => topLevel.value.find((c) => c.id === selectedId.value) ?? null)

function choose(id: Id) {
  selectedId.value = id
  query.value = ''
}

const results = computed<CatalogOption[]>(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  const options: CatalogOption[] = []
  for (const category of props.catalog) {
    if (offersAnyModel(category) && category.name.toLowerCase().includes(q))
      options.push({ key: optionKey(category), category })
    for (const model of category.models) {
      if (`${model.full_name} ${category.name}`.toLowerCase().includes(q)) {
        options.push({ key: optionKey(category, model), category, model })
      }
    }
  }
  return options
})
</script>

<template>
  <div class="browser">
    <!-- Search filters the whole catalog, so it heads the group list. -->
    <nav class="groups" role="tablist">
      <NInput
        v-if="!direct"
        v-model:value="query"
        class="search"
        clearable
        :placeholder="t('requests.new.searchPlaceholder')"
      >
        <template #prefix><Search :size="16" /></template>
      </NInput>
      <template v-for="group in tileGroups" :key="group.kind">
        <div class="group-heading eyebrow">{{ t(`enums.categoryKind.${group.kind}`) }}</div>
        <button
          v-for="category in group.items"
          :key="category.id"
          type="button"
          role="tab"
          class="group"
          :aria-selected="category.id === selectedId && !query.trim()"
          :class="{ active: category.id === selectedId && !query.trim() }"
          @click="choose(category.id)"
        >
          <component :is="categoryIcon(category.icon)" :size="18" :stroke-width="1.5" />
          <span class="name">{{ category.name }}</span>
        </button>
      </template>
      <!-- Own section at the end: anything the catalog does not list. -->
      <template v-if="!direct">
        <div class="group-heading eyebrow">{{ t('requests.new.otherSection') }}</div>
        <button
          type="button"
          role="tab"
          class="group"
          :aria-selected="selectedId === OTHER && !query.trim()"
          :class="{ active: selectedId === OTHER && !query.trim() }"
          @click="choose(OTHER)"
        >
          <MessageSquarePlus :size="18" :stroke-width="1.5" />
          <span class="name">{{ t('requests.new.otherTile') }}</span>
        </button>
      </template>
    </nav>

    <div class="main">
      <slot v-if="direct" name="direct" :category="selected" />
      <!-- Search results replace the group view while typing. -->
      <template v-else-if="query.trim()">
        <section class="results">
          <header>
            <h2>{{ t('requests.new.results') }}</h2>
            <span class="muted mono">{{ results.length }}</span>
          </header>
          <EmptyState v-if="!results.length" :text="t('requests.new.searchEmpty', { q: query })" />
          <CatalogOptionRow
            v-for="option in results"
            :key="option.key"
            :label="option.model ? option.model.full_name : anyModelLabel(option.category)"
            :hint="option.model ? option.category.name : undefined"
            :counts="optionCounts(option.category, option.model)"
            :in-cart="cartCounts[option.key] ?? 0"
            @add="emit('add', option.category, option.model)"
          />
        </section>
        <CustomRequestCard
          v-if="!results.length"
          :initial="query"
          @add="(text) => emit('addFreeText', text)"
        />
      </template>

      <template v-else>
        <slot />
        <CustomRequestCard v-if="selectedId === OTHER" @add="(text) => emit('addFreeText', text)" />
        <CategoryOptions
          v-if="selected"
          :category="selected"
          :children="childrenOf(selected.id)"
          :cart-counts="cartCounts"
          @add="(category, model) => emit('add', category, model)"
          @add-free-text="(text, category) => emit('addFreeText', text, category)"
        />
      </template>
    </div>
  </div>
</template>

<style scoped>
.browser {
  display: grid;
  grid-template-columns: 230px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}
.main {
  display: grid;
  gap: 14px;
  min-width: 0;
}
/* All columns are cards with the same top edge (period and cart on the right). */
.groups,
.results {
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
.groups {
  position: sticky;
  top: 16px;
  display: grid;
  gap: 2px;
  padding: 12px 10px;
}
.search {
  margin-bottom: 8px;
}
.group {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 10px;
  padding: 7px 10px;
  border: 1px solid transparent;
  border-radius: 3px;
  background: none;
  color: var(--ar-text-muted);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.group:hover {
  background: var(--ar-surface-sunken);
  color: var(--ar-text);
}
.group.active {
  border-color: color-mix(in srgb, var(--ar-primary) 35%, transparent);
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
.name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 500;
  color: var(--ar-text);
}
.group.active .name {
  color: var(--ar-primary);
}
.group-heading {
  margin: 10px 0 4px 10px;
}
.results {
  display: grid;
  padding: 18px 18px 6px;
}
.results header {
  display: flex;
  align-items: baseline;
  gap: 8px;
  margin-bottom: 6px;
}
.results h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
.results :deep(.option) {
  padding-inline: 0;
}
/* Narrow: groups as a wrapping list above the options. */
@media (max-width: 760px) {
  .browser {
    grid-template-columns: 1fr;
  }
  .groups {
    position: static;
    grid-template-columns: repeat(auto-fill, minmax(170px, 1fr));
  }
  .search,
  .group-heading {
    grid-column: 1 / -1;
  }
}
</style>
