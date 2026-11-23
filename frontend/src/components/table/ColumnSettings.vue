<script setup lang="ts">
import { Columns3, GripVertical, RotateCcw } from '@lucide/vue'
import {
  NButton,
  NCheckbox,
  NPopover,
  NRadioButton,
  NRadioGroup,
  type DataTableSize,
} from 'naive-ui'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import type { TableView } from '@/composables/useTableView'

/** Popover to show, hide and reorder the columns of a table and set its row density. */
const props = defineProps<{ view: TableView<any> }>()
const { t, locale } = useI18n()

/**
 * Order of the list: the shown columns as in the table, then the hidden ones alphabetically.
 * It is taken when the popover opens and kept while it is open, so a column switched on or
 * off stays where it is; the table follows the list.
 */
const order = ref<string[]>([])

function takeOrder() {
  const all = props.view.settingColumns.value
  const hidden = all
    .filter((c) => !c.visible)
    .sort((a, b) => a.title.localeCompare(b.title, locale.value))
  order.value = [...all.filter((c) => c.visible), ...hidden].map((c) => c.key)
}

const columns = computed(() => {
  const all = props.view.settingColumns.value
  const rank = (key: string) => {
    const index = order.value.indexOf(key)
    return index < 0 ? order.value.length : index
  }
  return [...all].sort((a, b) => rank(a.key) - rank(b.key))
})

/** Shows or hides a column; the table takes over the order of the list. */
function setVisible(key: string, visible: boolean) {
  props.view.setVisible(key, visible)
  props.view.setOrder(columns.value.map((c) => c.key))
}

function reset() {
  props.view.reset()
  takeOrder()
}
// The last visible column stays: a table without columns shows nothing.
const visibleCount = computed(() => columns.value.filter((c) => c.visible).length)

const dragging = ref<string | null>(null)
const over = ref<string | null>(null)

// Firefox only starts dragging with some data set.
function onDragStart(event: DragEvent, key: string) {
  dragging.value = key
  event.dataTransfer?.setData('text/plain', key)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDrop(target: string) {
  const keys = columns.value.map((c) => c.key)
  const movable = new Set(columns.value.filter((c) => c.movable).map((c) => c.key))
  const from = keys.indexOf(dragging.value ?? '')
  const to = keys.indexOf(target)
  if (from >= 0 && to >= 0 && from !== to && movable.has(target)) {
    keys.splice(to, 0, ...keys.splice(from, 1))
    order.value = keys
    props.view.setOrder(keys)
  }
  dragging.value = over.value = null
}
</script>

<template>
  <NPopover
    trigger="click"
    placement="bottom-end"
    :show-arrow="false"
    style="padding: 0"
    @update:show="(show: boolean) => show && takeOrder()"
  >
    <template #trigger>
      <NButton :title="t('table.columns')" :aria-label="t('table.columns')">
        <template #icon><Columns3 :size="16" /></template>
      </NButton>
    </template>
    <div class="column-settings">
      <div class="section-title">{{ t('table.columns') }}</div>
      <ul class="column-list">
        <!-- eslint-disable-next-line vuejs-accessibility/no-static-element-interactions -- reordering columns works by dragging only for now; a keyboard way is still missing -->
        <li
          v-for="column in columns"
          :key="column.key"
          :class="{ dragging: dragging === column.key, over: over === column.key }"
          :draggable="column.movable"
          @dragstart="onDragStart($event, column.key)"
          @dragend="dragging = over = null"
          @dragover.prevent="column.movable && (over = column.key)"
          @dragleave="over === column.key && (over = null)"
          @drop.prevent="onDrop(column.key)"
        >
          <GripVertical
            :size="14"
            :class="['grip', { hidden: !column.movable }]"
            :aria-hidden="true"
          />
          <NCheckbox
            :checked="column.visible"
            :disabled="!column.hideable || (column.visible && visibleCount <= 1)"
            @update:checked="(on: boolean) => setVisible(column.key, on)"
          >
            {{ column.title }}
          </NCheckbox>
        </li>
      </ul>
      <div class="hint">{{ t('table.columnsHint') }}</div>
      <div class="section-title">{{ t('table.density') }}</div>
      <NRadioGroup
        :value="view.density.value"
        size="small"
        @update:value="(d: DataTableSize) => view.setDensity(d)"
      >
        <NRadioButton value="small">{{ t('table.compact') }}</NRadioButton>
        <NRadioButton value="medium">{{ t('table.comfortable') }}</NRadioButton>
      </NRadioGroup>
      <NButton
        class="reset"
        size="small"
        quaternary
        :disabled="!view.customized.value"
        @click="reset"
      >
        <template #icon><RotateCcw :size="14" /></template>
        {{ t('table.resetView') }}
      </NButton>
    </div>
  </NPopover>
</template>

<style scoped>
.column-settings {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 260px;
  padding: 12px;
}
.section-title {
  color: var(--ar-text-muted);
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}
.column-list {
  max-height: min(560px, calc(100vh - 280px));
  margin: 0;
  padding: 0;
  overflow-y: auto;
  list-style: none;
}
.column-list li {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 3px 4px;
  border-top: 2px solid transparent;
  border-radius: 2px;
}
.column-list li[draggable='true'] {
  cursor: grab;
}
.column-list li.dragging {
  opacity: 0.4;
}
.column-list li.over {
  border-top-color: var(--ar-primary);
}
.grip {
  flex: none;
  color: var(--ar-text-subtle);
}
.grip.hidden {
  visibility: hidden;
}
.hint {
  color: var(--ar-text-subtle);
  font-size: 11px;
}
.reset {
  align-self: flex-start;
}
</style>
