<script setup lang="ts">
import { ArrowDown, ArrowUp, GripVertical, Scaling, X } from '@lucide/vue'
import { NButton, NPopover, type PopoverInst } from 'naive-ui'
import { ref, type Component } from 'vue'
import { useI18n } from 'vue-i18n'

import type { WidgetHeight, WidgetSettings, WidgetSize } from '@/types/accounts'

/**
 * Places a dashboard widget in the grid. While editing it adds a bar to move,
 * resize and remove it; the content itself then only reacts where `interactive`.
 */
defineProps<{
  title: string
  icon: Component
  settings: WidgetSettings
  editing?: boolean
  interactive?: boolean
  first?: boolean
  last?: boolean
}>()
const emit = defineEmits<{
  remove: []
  resize: [size: WidgetSize]
  setHeight: [height: WidgetHeight]
  move: [delta: number]
}>()

const { t } = useI18n()

/**
 * A new size moves the widget, sliding to its place (0.2s); the open size menu
 * follows its button frame by frame until it has settled.
 */
const sizeMenu = ref<PopoverInst | null>(null)
function followButton() {
  const until = performance.now() + 400
  const step = () => {
    sizeMenu.value?.syncPosition()
    if (performance.now() < until) requestAnimationFrame(step)
  }
  requestAnimationFrame(step)
}

function resize(size: WidgetSize) {
  emit('resize', size)
  followButton()
}

function setHeight(height: WidgetHeight) {
  emit('setHeight', height)
  followButton()
}
const SIZES: WidgetSize[] = ['small', 'medium', 'large']
const HEIGHTS: WidgetHeight[] = ['auto', 'small', 'medium', 'large']
</script>

<template>
  <div
    class="widget"
    :class="[`size-${settings.size}`, `height-${settings.height}`, { editing }]"
    :draggable="editing"
  >
    <div v-if="editing" class="edit-bar">
      <GripVertical :size="14" class="grip" />
      <component :is="icon" :size="14" />
      <span class="name">{{ title }}</span>
      <NPopover ref="sizeMenu" trigger="click" placement="bottom-end">
        <template #trigger>
          <NButton quaternary size="tiny" :title="t('dashboard.edit.size')">
            <template #icon><Scaling /></template>
            {{ t(`dashboard.edit.sizes.${settings.size}`) }} ·
            {{ t(`dashboard.edit.heights.${settings.height}`) }}
          </NButton>
        </template>
        <div class="size-menu">
          <span class="eyebrow">{{ t('dashboard.edit.width') }}</span>
          <div class="sizes" role="group" :aria-label="t('dashboard.edit.width')">
            <button
              v-for="size in SIZES"
              :key="size"
              type="button"
              :class="{ active: settings.size === size }"
              :aria-pressed="settings.size === size"
              @click="resize(size)"
            >
              {{ t(`dashboard.edit.sizes.${size}`) }}
            </button>
          </div>
          <span class="eyebrow">{{ t('dashboard.edit.height') }}</span>
          <div class="sizes" role="group" :aria-label="t('dashboard.edit.height')">
            <button
              v-for="height in HEIGHTS"
              :key="height"
              type="button"
              :class="{ active: settings.height === height }"
              :aria-pressed="settings.height === height"
              @click="setHeight(height)"
            >
              {{ t(`dashboard.edit.heights.${height}`) }}
            </button>
          </div>
        </div>
      </NPopover>
      <NButton
        quaternary
        size="tiny"
        :disabled="first"
        :title="t('dashboard.edit.moveUp')"
        @click="emit('move', -1)"
      >
        <template #icon><ArrowUp /></template>
      </NButton>
      <NButton
        quaternary
        size="tiny"
        :disabled="last"
        :title="t('dashboard.edit.moveDown')"
        @click="emit('move', 1)"
      >
        <template #icon><ArrowDown /></template>
      </NButton>
      <NButton quaternary size="tiny" :title="t('dashboard.edit.remove')" @click="emit('remove')">
        <template #icon><X /></template>
      </NButton>
    </div>
    <div class="content" :inert="editing && !interactive">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.widget {
  display: flex;
  flex-direction: column;
  min-width: 0;
}
.widget.size-small {
  grid-column: span 2;
}
.widget.size-medium {
  grid-column: span 3;
}
.widget.size-large {
  grid-column: span 6;
}
.content {
  flex: 1;
  min-width: 0;
  /* Widgets adapt to their own width, not the window's. */
  container-type: inline-size;
}
.content > :deep(*) {
  height: 100%;
}
/* A fixed height: the widget no longer stretches with its row, its content scrolls. */
.widget:not(.height-auto) {
  align-self: start;
}
.widget.height-small .content {
  flex: none;
  height: 240px;
}
.widget.height-medium .content {
  flex: none;
  height: 380px;
}
.widget.height-large .content {
  flex: none;
  height: 540px;
}
.widget:not(.height-auto) .content :deep(.n-card-content),
.widget:not(.height-auto) .content :deep(.tiles) {
  min-height: 0;
  overflow: auto;
}
.widget.editing {
  padding: 6px;
  border: 1px dashed var(--ar-border-strong, var(--ar-border));
  border-radius: 4px;
  background: var(--ar-surface-sunken);
  cursor: grab;
}
.widget.editing:active {
  cursor: grabbing;
}
.edit-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  min-height: 28px;
  padding: 0 2px 6px;
  font-size: 12px;
}
.grip {
  color: var(--ar-text-subtle);
}
.name {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  font-weight: 600;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.size-menu {
  display: grid;
  justify-items: start;
  gap: 6px;
  padding: 2px;
}
.size-menu .eyebrow + .sizes {
  margin-bottom: 4px;
}
.sizes {
  display: inline-flex;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  overflow: hidden;
}
.sizes button {
  padding: 2px 8px;
  border: none;
  background: var(--ar-surface);
  color: var(--ar-text-subtle);
  font: inherit;
  cursor: pointer;
}
.sizes button + button {
  border-left: 1px solid var(--ar-border);
}
.sizes button:hover {
  color: var(--ar-text);
}
.sizes button.active {
  background: var(--ar-primary);
  color: var(--ar-surface);
}
@media (max-width: 1100px) {
  .widget.size-small {
    grid-column: span 3;
  }
}
@media (max-width: 760px) {
  .widget.size-small,
  .widget.size-medium {
    grid-column: span 6;
  }
}
</style>
