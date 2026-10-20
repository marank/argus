<script setup lang="ts">
import { ArrowDown, ArrowUp, Eye, EyeOff, GripVertical } from '@lucide/vue'
import { NButton } from 'naive-ui'
import type { Component } from 'vue'
import { useI18n } from 'vue-i18n'

import type { WidgetSettings, WidgetSize } from '@/types/accounts'

/**
 * Places a dashboard widget in the grid. While editing it adds a bar to move,
 * resize and hide it; the content itself then only reacts where `interactive`.
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
const emit = defineEmits<{ toggle: []; resize: [size: WidgetSize]; move: [delta: number] }>()

const { t } = useI18n()
const SIZES: WidgetSize[] = ['small', 'medium', 'large']
</script>

<template>
  <div
    class="widget"
    :class="[`size-${settings.size}`, { editing, off: !settings.visible }]"
    :draggable="editing"
  >
    <div v-if="editing" class="edit-bar">
      <GripVertical :size="14" class="grip" />
      <component :is="icon" :size="14" />
      <span class="name">{{ title }}</span>
      <div class="sizes" role="group" :aria-label="t('dashboard.edit.width')">
        <button
          v-for="size in SIZES"
          :key="size"
          type="button"
          :class="{ active: settings.size === size }"
          :aria-pressed="settings.size === size"
          @click="emit('resize', size)"
        >
          {{ t(`dashboard.edit.sizes.${size}`) }}
        </button>
      </div>
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
      <NButton
        quaternary
        size="tiny"
        :type="settings.visible ? 'default' : 'primary'"
        :title="settings.visible ? t('dashboard.edit.hide') : t('dashboard.edit.show')"
        @click="emit('toggle')"
      >
        <template #icon><component :is="settings.visible ? Eye : EyeOff" /></template>
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
}
.content > :deep(*) {
  height: 100%;
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
.widget.off .content {
  opacity: 0.35;
  filter: grayscale(1);
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
.widget.off .name {
  color: var(--ar-text-subtle);
  text-decoration: line-through;
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
  .sizes {
    display: none;
  }
}
</style>
