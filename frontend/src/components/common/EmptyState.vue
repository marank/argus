<script setup lang="ts">
import { Inbox } from '@lucide/vue'
import type { Component } from 'vue'

defineProps<{ text: string; icon?: Component }>()
</script>

<template>
  <div class="empty">
    <component :is="icon ?? Inbox" :size="28" :stroke-width="1.4" />
    <p>{{ text }}</p>
    <slot />
  </div>
</template>

<style scoped>
.empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 40px 16px;
  color: var(--ar-text-subtle);
  border: 1px dashed var(--ar-border);
  border-radius: 3px;
  text-align: center;
}
p {
  margin: 0;
  color: var(--ar-text-muted);
}
</style>
