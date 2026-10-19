<script setup lang="ts">
import { MessageSquarePlus, Search } from '@lucide/vue'
import { NInput } from 'naive-ui'
import { computed, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import EmptyState from '@/components/common/EmptyState.vue'
import type { Id } from '@/types/common'
import type { CatalogCategory, CatalogModel } from '@/types/reservations'
import { categoryIcon } from '@/utils/icons'
import { anyModelLabel } from '@/utils/reservations'

import CatalogOptionRow from './CatalogOptionRow.vue'
import CategoryOptions from './CategoryOptions.vue'
import CustomRequestCard from './CustomRequestCard.vue'
import { offersAnyModel, optionKey, optionCounts, type CatalogOption } from './types'

/**
 * Catalog with search: device groups as compact tiles, only the selected group
 * shows its options. Accessory groups appear inside their parent group.
 */
const props = defineProps<{ catalog: CatalogCategory[]; cartCounts: Record<string, number> }>()
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
    <NInput
      v-model:value="query"
      size="large"
      clearable
      :placeholder="t('reservations.new.searchPlaceholder')"
    >
      <template #prefix><Search :size="18" /></template>
    </NInput>

    <!-- Search results replace the group view while typing. -->
    <template v-if="query.trim()">
      <div class="eyebrow">{{ t('reservations.new.results') }}</div>
      <template v-if="!results.length">
        <EmptyState :text="t('reservations.new.searchEmpty', { q: query })" />
        <CustomRequestCard :initial="query" @add="(text) => emit('addFreeText', text)" />
      </template>
      <div v-else class="results">
        <CatalogOptionRow
          v-for="option in results"
          :key="option.key"
          :label="option.model ? option.model.full_name : anyModelLabel(option.category)"
          :hint="option.model ? option.category.name : undefined"
          :counts="optionCounts(option.category, option.model)"
          :in-cart="cartCounts[option.key] ?? 0"
          @add="emit('add', option.category, option.model)"
        />
      </div>
    </template>

    <template v-else>
      <div class="tiles" role="tablist">
        <template v-for="group in tileGroups" :key="group.kind">
          <div class="tile-heading eyebrow">
            {{ t(`enums.categoryKind.${group.kind}`) }}
          </div>
          <button
            v-for="category in group.items"
            :key="category.id"
            type="button"
            role="tab"
            class="tile"
            :aria-selected="category.id === selectedId"
            :class="{ active: category.id === selectedId }"
            @click="selectedId = category.id"
          >
            <component :is="categoryIcon(category.icon)" :size="20" :stroke-width="1.5" />
            <span class="name">{{ category.name }}</span>
          </button>
        </template>
        <!-- Own section at the end: anything the catalog does not list. -->
        <div class="tile-heading eyebrow">{{ t('reservations.new.otherSection') }}</div>
        <button
          type="button"
          role="tab"
          class="tile other"
          :aria-selected="selectedId === OTHER"
          :class="{ active: selectedId === OTHER }"
          @click="selectedId = OTHER"
        >
          <MessageSquarePlus :size="20" :stroke-width="1.5" />
          <span class="name">{{ t('reservations.new.otherTile') }}</span>
        </button>
      </div>
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
</template>

<style scoped>
.browser {
  display: grid;
  gap: 14px;
}
.tiles {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(210px, 1fr));
  gap: 8px;
}
.tile {
  display: grid;
  grid-template-columns: auto 1fr;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  color: var(--ar-text-muted);
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.tile:hover {
  border-color: var(--ar-border-strong);
  color: var(--ar-text);
}
.tile.active {
  border-color: var(--ar-primary);
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
.name {
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  overflow: hidden;
  line-height: 1.3;
  font-weight: 500;
  color: var(--ar-text);
}
.tile-heading {
  grid-column: 1 / -1;
  margin-top: 4px;
}
.tile.other {
  border-style: dashed;
}
.tile.active .name {
  color: var(--ar-primary);
}
.results {
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
</style>
