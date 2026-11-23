<script setup lang="ts">
import { ChevronRight, MessageSquarePlus, PackageCheck, Search } from '@lucide/vue'
import { useMediaQuery } from '@vueuse/core'
import { NInput } from 'naive-ui'
import { computed, nextTick, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import EmptyState from '@/components/common/EmptyState.vue'
import type { Id } from '@/types/common'
import { categoryIcon } from '@/utils/icons'
import { anyModelLabel } from '@/utils/requests'
import { scrollerOf } from '@/utils/scroll'

import CatalogOptionRow from './CatalogOptionRow.vue'
import CategoryOptions from './CategoryOptions.vue'
import CustomRequestCard from './CustomRequestCard.vue'
import {
  offersAnyModel,
  offersSpecificModel,
  optionKey,
  optionCounts,
  type CatalogOption,
} from './types'

/**
 * Catalog with search on top, below in two columns: all groups as a list on the
 * left, the selected group's options (or the search results) next to it. Accessory groups appear inside their
 * parent group. With `fitting` (how many devices have something that fits), a virtual group
 * "For your devices" comes first; the `fitting` slot shows its content.
 * For a direct hand-out (`direct`) the `direct` slot replaces search and options;
 * the groups on the left then browse what is in stock.
 */
const props = defineProps<{
  catalog: Schemas['CatalogCategoryOut'][]
  cartCounts: Record<string, number>
  direct?: boolean
  /** The employee's devices with something in the catalog that fits them. */
  fitting?: number
}>()
const emit = defineEmits<{
  add: [category: Schemas['CatalogCategoryOut'], model?: Schemas['CatalogModelOut']]
  remove: [category: Schemas['CatalogCategoryOut'], model?: Schemas['CatalogModelOut']]
  addFreeText: [text: string, category?: Schemas['CatalogCategoryOut']]
}>()
const { t } = useI18n()

const query = ref('')
const topLevel = computed(() => {
  const ids = new Set(props.catalog.map((c) => c.id))
  return props.catalog.filter((c) => !c.parent_id || !ids.has(c.parent_id))
})
/** All subcategories below a group, each followed by its own, at any depth. */
function descendantsOf(id: Id): Schemas['CatalogCategoryOut'][] {
  return props.catalog
    .filter((c) => c.parent_id === id)
    .flatMap((child) => [child, ...descendantsOf(child.id)])
}
/** Tiles split into hardware and software, followed by the section for anything else. */
const tileGroups = computed(() =>
  (['hardware', 'software'] as const)
    // Direct hand-outs are for devices and consumables, not license seats.
    .filter((kind) => !props.direct || kind === 'hardware')
    .map((kind) => ({ kind, items: topLevel.value.filter((c) => c.kind === kind) }))
    .filter((group) => group.items.length),
)

/** Pseudo selections: the "something else" tile and the virtual group "For your devices". */
const OTHER = 'other'
const FITTING = 'fitting'
const showsFitting = computed(() => !props.direct && !!props.fitting)
const selectedId = ref<Id | null>(null)
// What fits one's own devices is the likeliest wish: it opens first where it exists.
watch(
  [topLevel, showsFitting],
  ([groups, fits]) => {
    if (selectedId.value) return
    if (fits) selectedId.value = FITTING
    else if (groups.length) selectedId.value = groups[0]!.id
  },
  { immediate: true },
)
const selected = computed(() => topLevel.value.find((c) => c.id === selectedId.value) ?? null)

/**
 * Phones show one level at a time, like a menu: first the groups as cards, then the
 * chosen group's options; the page's header leads back. Wide screens show both side by side.
 */
const narrow = useMediaQuery('(max-width: 760px)')
/** On a phone: one group is open (level two) instead of the overview of all groups. */
const opened = defineModel<boolean>('opened', { default: false })
const root = ref<HTMLElement | null>(null)
const searching = computed(() => !!query.value.trim())
/** Level one on a phone: search and the groups (or, while typing, the results). */
const overview = computed(() => narrow.value && !opened.value)

/**
 * A group opens at its top; back in the overview, the list is where it was left.
 * Only on a phone: there the levels replace each other.
 */
let overviewScroll = 0
watch(opened, (isOpen) => {
  if (!narrow.value) return
  const scroller = scrollerOf(root.value)
  if (isOpen) overviewScroll = scroller?.scrollTop ?? 0
  void nextTick(() => scroller?.scrollTo({ top: isOpen ? 0 : overviewScroll }))
})

function choose(id: Id) {
  selectedId.value = id
  query.value = ''
  opened.value = true
}

/** The open group, for the page's header on a phone. */
const selectedName = computed(() => {
  if (selectedId.value === OTHER) return t('requests.new.otherTile')
  if (selectedId.value === FITTING) return t('requests.new.quickPick')
  return selected.value?.name ?? ''
})
defineExpose({ selectedName })

const results = computed<CatalogOption[]>(() => {
  const q = query.value.trim().toLowerCase()
  if (!q) return []
  const options: CatalogOption[] = []
  for (const category of props.catalog) {
    const models = category.models.filter((m) =>
      `${m.full_name} ${category.name}`.toLowerCase().includes(q),
    )
    // Where IT picks the model, a hit on one of them offers the group.
    const anyHit = offersSpecificModel(category)
      ? category.name.toLowerCase().includes(q)
      : models.length > 0
    if (offersAnyModel(category) && anyHit) options.push({ key: optionKey(category), category })
    if (!offersSpecificModel(category)) continue
    for (const model of models) options.push({ key: optionKey(category, model), category, model })
  }
  return options
})
</script>

<template>
  <div ref="root" class="browser">
    <!-- Search filters the whole catalog, so it heads the group list. -->
    <!-- On a phone the overview only ever comes back: it enters from the left. -->
    <Transition name="ar-back">
      <nav v-show="!narrow || overview" class="groups" role="tablist">
        <NInput
          v-if="!direct"
          v-model:value="query"
          class="search"
          clearable
          :placeholder="t('requests.new.searchPlaceholder')"
        >
          <template #prefix><Search :size="16" /></template>
        </NInput>
        <!-- On a phone: cards that open their group, like a menu. -->
        <div v-show="!(narrow && searching)" class="group-list">
          <button
            v-if="showsFitting"
            type="button"
            role="tab"
            class="group fitting"
            :aria-selected="selectedId === FITTING && !query.trim()"
            :class="{ active: selectedId === FITTING && !query.trim() }"
            @click="choose(FITTING)"
          >
            <PackageCheck :size="18" :stroke-width="1.5" />
            <span class="name">{{ t('requests.new.quickPick') }}</span>
            <span class="fitting-count mono">{{ fitting }}</span>
            <ChevronRight class="go" :size="16" />
          </button>
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
              <ChevronRight class="go" :size="16" />
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
              <ChevronRight class="go" :size="16" />
            </button>
          </template>
        </div>
      </nav>
    </Transition>

    <!-- A group comes in from the right; search results just fade in under the field. -->
    <Transition :name="searching ? 'ar-fade' : 'ar-forward'">
      <div v-show="!overview || searching" class="main">
        <slot v-if="direct" name="direct" :category="selected" />
        <!-- Search results replace the group view while typing. -->
        <template v-else-if="query.trim()">
          <section class="results">
            <header>
              <h2>{{ t('requests.new.results') }}</h2>
              <span class="muted mono">{{ results.length }}</span>
            </header>
            <EmptyState
              v-if="!results.length"
              :text="t('requests.new.searchEmpty', { q: query })"
            />
            <CatalogOptionRow
              v-for="option in results"
              :key="option.key"
              :label="option.model ? option.model.full_name : anyModelLabel(option.category)"
              :hint="option.model ? option.category.name : undefined"
              :counts="optionCounts(option.category, option.model)"
              :in-cart="cartCounts[option.key] ?? 0"
              @add="emit('add', option.category, option.model)"
              @remove="emit('remove', option.category, option.model)"
            />
          </section>
          <CustomRequestCard
            v-if="!results.length"
            :initial="query"
            @add="(text) => emit('addFreeText', text)"
          />
        </template>

        <template v-else>
          <slot v-if="selectedId === FITTING" name="fitting" />
          <CustomRequestCard
            v-if="selectedId === OTHER"
            @add="(text) => emit('addFreeText', text)"
          />
          <CategoryOptions
            v-if="selected"
            :category="selected"
            :children="descendantsOf(selected.id)"
            :catalog="catalog"
            :cart-counts="cartCounts"
            @add="(category, model) => emit('add', category, model)"
            @remove="(category, model) => emit('remove', category, model)"
            @add-free-text="(text, category) => emit('addFreeText', text, category)"
          />
        </template>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.browser {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  gap: 14px;
  align-items: start;
}
/* The options adapt to this column, not to the window (see CatalogOptionRow). */
.main {
  container: catalog / inline-size;
  display: grid;
  grid-template-columns: minmax(0, 1fr);
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
  /* Below a fixed header of the page, if it has one (--sticky-top). */
  top: calc(var(--sticky-top, 0px) + 16px);
  padding: 12px 10px;
}
.group-list {
  display: grid;
  gap: 2px;
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
/* A narrow column: long names wrap instead of being cut. */
.name {
  overflow-wrap: anywhere;
  line-height: 1.25;
  font-weight: 500;
  color: var(--ar-text);
}
.group.active .name {
  color: var(--ar-primary);
}
/* The virtual group stands apart a little: tinted, with how many devices it covers. */
.group.fitting {
  grid-template-columns: auto minmax(0, 1fr) auto;
  margin-bottom: 4px;
}
/* Its name is longer than a group's: it may wrap instead of being cut. */
.group.fitting .name {
  white-space: normal;
  line-height: 1.25;
}
.fitting-count {
  padding: 0 6px;
  border-radius: 999px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
  font-size: 11px;
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
.go {
  display: none;
}
/* Narrow: a menu in two levels, the groups as cards first, then one group's options. */
@media (max-width: 760px) {
  .browser {
    grid-template-columns: minmax(0, 1fr);
    gap: 12px;
  }
  .groups {
    position: static;
    min-width: 0;
    padding: 0;
    border: none;
    background: none;
  }
  .search {
    margin-bottom: 4px;
  }
  .group-list {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 8px;
  }
}
/* Small phones: one card per row, a plain menu list. */
@media (max-width: 480px) {
  .group-list {
    grid-template-columns: minmax(0, 1fr);
    gap: 6px;
  }
}
@media (max-width: 760px) {
  .group-heading {
    grid-column: 1 / -1;
    margin: 10px 0 0 2px;
  }
  .group.fitting,
  .group.fitting.active {
    grid-template-columns: auto minmax(0, 1fr) auto auto;
    margin-bottom: 0;
    border-color: color-mix(in srgb, var(--ar-primary) 35%, var(--ar-border));
    background: var(--ar-primary-soft);
  }
  .group {
    grid-template-columns: auto minmax(0, 1fr) auto;
    gap: 8px;
    min-height: 52px;
    padding: 10px 10px 10px 12px;
    border-color: var(--ar-border);
    background: var(--ar-surface);
    color: var(--ar-primary);
  }
  .group:active {
    background: var(--ar-surface-sunken);
  }
  /* No selection to show here: a card opens its group. */
  .group.active {
    border-color: var(--ar-border);
    background: var(--ar-surface);
  }
  .group.active .name {
    color: var(--ar-text);
  }
  .name {
    white-space: normal;
    line-height: 1.25;
  }
  .go {
    display: block;
    color: var(--ar-text-subtle);
  }
  /* The page's header names the open group already. */
  .main :deep(.options > header .icon),
  .main :deep(.options > header h2) {
    display: none;
  }
}
</style>
