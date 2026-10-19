<script setup lang="ts">
import { computed } from 'vue'
import { useI18n } from 'vue-i18n'

import type { CatalogCategory, CatalogModel } from '@/types/reservations'
import { categoryIcon } from '@/utils/icons'
import { anyModelLabel } from '@/utils/reservations'

import CatalogOptionRow from './CatalogOptionRow.vue'
import FreeTextOption from './FreeTextOption.vue'
import { offersAnyModel, optionKey, optionCounts } from './types'

/** Options of one device group: "any device" first, then specific models, then accessories. */
const props = defineProps<{
  category: CatalogCategory
  children: CatalogCategory[]
  cartCounts: Record<string, number>
}>()
const emit = defineEmits<{
  add: [category: CatalogCategory, model?: CatalogModel]
  addFreeText: [text: string, category: CatalogCategory]
}>()
const { t } = useI18n()

const groups = computed(() => [props.category, ...props.children])
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

    <section v-for="group in groups" :key="group.id" class="group">
      <div v-if="group.id !== category.id" class="eyebrow">
        {{ t('reservations.new.accessories', { name: group.name }) }}
      </div>
      <CatalogOptionRow
        v-if="offersAnyModel(group)"
        primary
        :label="anyModelLabel(group)"
        :counts="optionCounts(group)"
        :in-cart="cartCounts[optionKey(group)] ?? 0"
        @add="emit('add', group)"
      />
      <template v-if="group.models.length">
        <div v-if="offersAnyModel(group)" class="eyebrow sub">
          {{ t('reservations.new.specificModel') }}
        </div>
        <div class="models">
          <CatalogOptionRow
            v-for="model in group.models"
            :key="model.id"
            :label="model.full_name"
            :hint="model.description"
            :counts="optionCounts(group, model)"
            :in-cart="cartCounts[optionKey(group, model)] ?? 0"
            @add="emit('add', group, model)"
          />
        </div>
      </template>
    </section>

    <FreeTextOption
      :title="t('reservations.new.otherInGroup', { category: category.name })"
      :hint="t('reservations.new.otherHint')"
      :placeholder="t('reservations.new.otherInGroupPlaceholder')"
      @add="(text) => emit('addFreeText', text, category)"
    />
  </div>
</template>

<style scoped>
.options {
  display: grid;
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
.group + .group {
  padding-top: 16px;
  border-top: 1px solid var(--ar-border);
}
.sub {
  margin-top: 6px;
}
.models {
  border: 1px solid var(--ar-border);
  border-radius: 3px;
}
</style>
