<script setup lang="ts">
import type { Component } from 'vue'

/**
 * A titled panel of related stat cards side by side. `count` (visible cards)
 * sets how much width the panel takes next to its neighbours.
 */
/** `wide`: takes a row of its own. */
defineProps<{ title: string; icon?: Component; count: number; wide?: boolean }>()
</script>

<template>
  <section class="stat-group" :class="{ wide }" :style="{ '--count': count }">
    <header class="eyebrow">
      <component :is="icon" v-if="icon" :size="13" />
      {{ title }}
    </header>
    <div class="tiles">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.stat-group {
  display: grid;
  grid-template-rows: auto 1fr;
  flex: var(--count) 1 calc(var(--count) * 112px);
}
.stat-group.wide {
  flex-basis: 100%;
  min-width: 0;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
header {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 9px 14px;
  border-bottom: 1px solid var(--ar-border);
}
.tiles {
  display: grid;
  grid-template-columns: repeat(var(--count), minmax(0, 1fr));
}
/* Cards inside a panel: no own frame, thin dividers, the tone as a short top mark. */
.tiles :deep(.stat) {
  /* Numbers line up at the bottom, however many lines the labels take. */
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  border: none;
  border-radius: 0;
  background: transparent;
}
.tiles :deep(.stat + .stat) {
  border-left: 1px solid var(--ar-border);
}
.tiles :deep(.stat::before) {
  inset: 0 auto auto 14px;
  width: 22px;
  height: 3px;
  border-radius: 0 0 2px 2px;
}
.tiles :deep(a.stat:hover) {
  background: var(--ar-surface-sunken);
}
@media (max-width: 720px) {
  .tiles {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .tiles :deep(.stat:nth-child(odd)) {
    border-left: none;
  }
}
</style>
