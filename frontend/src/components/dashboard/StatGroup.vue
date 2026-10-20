<script setup lang="ts">
import type { Component } from 'vue'

/**
 * A titled panel of related stat cards side by side. `count` (visible cards)
 * sets the number of columns; a narrow panel shows two per row.
 */
defineProps<{ title: string; icon?: Component; count: number }>()
</script>

<template>
  <section class="stat-group" :style="{ '--count': count }">
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
  height: 100%;
  min-width: 0;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  container-type: inline-size;
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
  height: 100%;
  border: none;
  border-radius: 0;
  background: transparent;
}
.tiles > :deep(* + *) {
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
@container (max-width: 520px) {
  .tiles {
    grid-template-columns: repeat(min(var(--count), 2), minmax(0, 1fr));
  }
  .tiles > :deep(:nth-child(odd)) {
    border-left: none;
  }
  .tiles > :deep(:nth-child(n + 3)) {
    border-top: 1px solid var(--ar-border);
  }
}
</style>
