<script setup lang="ts">
import { Plug } from '@lucide/vue'
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { Schemas } from '@/api/types'
import type { Id } from '@/types/common'
import { categoryIcon } from '@/utils/icons'
import { anyModelLabel } from '@/utils/requests'

import CatalogOptionRow from './CatalogOptionRow.vue'
import FreeTextOption from './FreeTextOption.vue'
import {
  offersAnyModel,
  offersSpecificModel,
  optionKey,
  optionCounts,
  type CatalogOption,
} from './types'

/**
 * Options of one device group: "any device" first, then the specific models, then the
 * subcategories, then one block with the accessories: the subcategories marked as such and the
 * models of accessory categories compatible with the group's models.
 */
const props = defineProps<{
  category: Schemas['CatalogCategoryOut']
  children: Schemas['CatalogCategoryOut'][]
  /** The whole catalog, to find the compatible accessories in other categories. */
  catalog: Schemas['CatalogCategoryOut'][]
  cartCounts: Record<string, number>
}>()
const emit = defineEmits<{
  add: [category: Schemas['CatalogCategoryOut'], model?: Schemas['CatalogModelOut']]
  remove: [category: Schemas['CatalogCategoryOut'], model?: Schemas['CatalogModelOut']]
  addFreeText: [text: string, category: Schemas['CatalogCategoryOut']]
}>()
const { t } = useI18n()

/** Every model of the catalog with its category. */
const byModel = computed(() => {
  const map = new Map<
    Id,
    { category: Schemas['CatalogCategoryOut']; model: Schemas['CatalogModelOut'] }
  >()
  for (const category of props.catalog) {
    for (const model of category.models) map.set(model.id, { category, model })
  }
  return map
})

/** The devices an accessory fits, e.g. on the page of an accessory category. */
const fitsAll = computed(() => {
  const map = new Map<Id, string[]>()
  for (const { model } of byModel.value.values()) {
    for (const id of model.accessories) map.set(id, [...(map.get(id) ?? []), model.full_name])
  }
  return map
})

function hint(...parts: (string | undefined)[]): string | undefined {
  return parts.filter(Boolean).join(' · ') || undefined
}

function modelHint(model: Schemas['CatalogModelOut']): string | undefined {
  const fits = props.category.holds_accessories ? fitsAll.value.get(model.id) : undefined
  return hint(model.description, fits && t('requests.new.fitsTo', { models: fits.join(', ') }))
}

/** Below the first level, the way down from the group: "Scanner accessories / Cradles". */
function path(group: Schemas['CatalogCategoryOut']): string {
  const byId = new Map(props.catalog.map((g) => [g.id, g]))
  const names = [group.name]
  let parent = group.parent_id ? byId.get(group.parent_id) : undefined
  while (parent && parent.id !== props.category.id) {
    names.unshift(parent.name)
    parent = parent.parent_id ? byId.get(parent.parent_id) : undefined
  }
  return names.join(' / ')
}

interface AccessoryOption extends CatalogOption {
  /** Models of this group the accessory is compatible with. */
  fits: string[]
}
interface AccessoryGroup {
  category: Schemas['CatalogCategoryOut']
  options: AccessoryOption[]
}

/** What a group offers: any device of it, its models, or both (see the category's choice). */
function optionsOf(group: Schemas['CatalogCategoryOut']): AccessoryOption[] {
  return [
    ...(offersAnyModel(group) ? [{ key: optionKey(group), category: group, fits: [] }] : []),
    ...(offersSpecificModel(group)
      ? group.models.map((model) => ({
          key: optionKey(group, model),
          category: group,
          model,
          fits: [],
        }))
      : []),
  ]
}

/**
 * Subcategories in the accessories block: those marked as accessories, unless the page is an
 * accessory category itself (then they are just its subgroups).
 */
const isAccessoryGroup = (group: Schemas['CatalogCategoryOut']) =>
  group.holds_accessories && !props.category.holds_accessories

/** The other subcategories, as groups of their own (e.g. "Laptops / 14 inch"). */
const subgroups = computed<AccessoryGroup[]>(() =>
  props.children
    .filter((group) => !isAccessoryGroup(group))
    .map((group) => ({ category: group, options: optionsOf(group) }))
    .filter((group) => group.options.length),
)

/**
 * The accessories, grouped by their category in catalog order. A group gets a heading only
 * when it has more than one option; a single option names its group in the hint instead.
 */
const accessories = computed<AccessoryGroup[]>(() => {
  const options = new Map<string, AccessoryOption>()
  const add = (category: Schemas['CatalogCategoryOut'], model?: Schemas['CatalogModelOut']) => {
    const key = optionKey(category, model)
    if (!options.has(key)) options.set(key, { key, category, model, fits: [] })
    return options.get(key)!
  }
  for (const device of props.category.models) {
    for (const id of device.accessories) {
      const entry = byModel.value.get(id)
      if (!entry) continue
      // Where IT picks the model, the accessory is offered as "any" of its category.
      const model = offersSpecificModel(entry.category) ? entry.model : undefined
      add(entry.category, model).fits.push(device.full_name)
    }
  }
  for (const group of props.children.filter(isAccessoryGroup)) {
    for (const option of optionsOf(group)) add(option.category, option.model)
  }
  const order = new Map(props.catalog.map((c, index) => [c.id, index]))
  const groups = new Map<Id, AccessoryGroup>()
  for (const option of options.values()) {
    const group = groups.get(option.category.id) ?? { category: option.category, options: [] }
    group.options.push(option)
    groups.set(option.category.id, group)
  }
  return [...groups.values()].sort(
    (a, b) => (order.get(a.category.id) ?? 0) - (order.get(b.category.id) ?? 0),
  )
})

/** A group's name goes into the hint of its only option instead of a heading of its own. */
function groupHint(group: AccessoryGroup, option: AccessoryOption): string | undefined {
  return hint(
    group.options.length === 1 ? path(group.category) : undefined,
    option.model?.description,
  )
}

function accessoryHint(group: AccessoryGroup, option: AccessoryOption): string | undefined {
  // Fitting every model of the group goes without saying.
  const narrows = option.fits.length && option.fits.length < props.category.models.length
  return hint(
    group.options.length === 1 ? path(group.category) : undefined,
    option.model?.description,
    narrows ? t('requests.new.fitsTo', { models: option.fits.join(', ') }) : undefined,
  )
}
</script>

<template>
  <div class="options">
    <header>
      <span class="icon"
        ><component :is="categoryIcon(category.icon)" :size="22" :stroke-width="1.5"
      /></span>
      <div>
        <h2>{{ category.name }}</h2>
        <p v-if="category.description" class="muted">{{ category.description }}</p>
      </div>
    </header>

    <section
      v-if="offersAnyModel(category) || (offersSpecificModel(category) && category.models.length)"
      class="group"
    >
      <CatalogOptionRow
        v-if="offersAnyModel(category)"
        primary
        :label="anyModelLabel(category)"
        :counts="optionCounts(category)"
        :in-cart="cartCounts[optionKey(category)] ?? 0"
        @add="emit('add', category)"
        @remove="emit('remove', category)"
      />
      <template v-if="offersSpecificModel(category) && category.models.length">
        <div v-if="offersAnyModel(category)" class="eyebrow sub">
          {{ t('requests.new.specificModel') }}
        </div>
        <div class="models">
          <CatalogOptionRow
            v-for="model in category.models"
            :key="model.id"
            :label="model.full_name"
            :hint="modelHint(model)"
            :counts="optionCounts(category, model)"
            :in-cart="cartCounts[optionKey(category, model)] ?? 0"
            @add="emit('add', category, model)"
            @remove="emit('remove', category, model)"
          />
        </div>
      </template>
    </section>

    <section v-if="subgroups.length" class="group">
      <div class="models">
        <template v-for="group in subgroups" :key="group.category.id">
          <div v-if="group.options.length > 1" class="sub-heading">{{ path(group.category) }}</div>
          <CatalogOptionRow
            v-for="option in group.options"
            :key="option.key"
            :label="option.model ? option.model.full_name : anyModelLabel(option.category)"
            :hint="groupHint(group, option)"
            :counts="optionCounts(option.category, option.model)"
            :in-cart="cartCounts[option.key] ?? 0"
            @add="emit('add', option.category, option.model)"
            @remove="emit('remove', option.category, option.model)"
          />
        </template>
      </div>
    </section>

    <section v-if="accessories.length" class="accessories">
      <h3><Plug :size="15" :stroke-width="1.75" />{{ t('requests.new.accessories') }}</h3>
      <div class="models">
        <template v-for="group in accessories" :key="group.category.id">
          <div v-if="group.options.length > 1" class="sub-heading">{{ path(group.category) }}</div>
          <CatalogOptionRow
            v-for="option in group.options"
            :key="option.key"
            :label="option.model ? option.model.full_name : anyModelLabel(option.category)"
            :hint="accessoryHint(group, option)"
            :counts="optionCounts(option.category, option.model)"
            :in-cart="cartCounts[option.key] ?? 0"
            @add="emit('add', option.category, option.model)"
            @remove="emit('remove', option.category, option.model)"
          />
        </template>
      </div>
    </section>

    <FreeTextOption
      :title="t('requests.new.otherInGroup', { category: category.name })"
      :hint="t('requests.new.otherHint')"
      :placeholder="t('requests.new.otherInGroupPlaceholder')"
      @add="(text) => emit('addFreeText', text, category)"
    />
  </div>
</template>

<style scoped>
.options {
  display: grid;
  grid-template-columns: minmax(0, 1fr);
  gap: 18px;
  padding: 18px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 3px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
}
h2 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
}
header p {
  margin: 2px 0 0;
}
.group {
  display: grid;
  gap: 8px;
}
.sub {
  margin-top: 6px;
}
.models {
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
/* Accessories as one block of their own, set off from the devices. */
.accessories {
  display: grid;
  gap: 10px;
  padding: 12px;
  border-radius: 3px;
  background: var(--ar-surface-sunken);
}
h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  color: var(--ar-text-muted);
  font-size: 13px;
  font-weight: 600;
}
.sub-heading {
  padding: 8px 12px 2px;
  color: var(--ar-text-subtle);
  font-size: 11.5px;
  font-weight: 600;
}
.sub-heading:not(:first-child) {
  border-top: 1px solid var(--ar-border);
}
/* The heading is the top of its group: no line between it and its first option. */
.models :deep(.option:has(+ .sub-heading)) {
  border-bottom: none;
}
@container catalog (max-width: 480px) {
  .options {
    gap: 14px;
    padding: 12px;
  }
  .icon {
    width: 32px;
    height: 32px;
  }
  .accessories {
    padding: 8px;
  }
}
</style>
