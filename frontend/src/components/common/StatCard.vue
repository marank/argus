<script setup lang="ts">
import type { Component } from 'vue'
import type { RouteLocationRaw } from 'vue-router'

import type { Tone } from '@/utils/status'

defineProps<{
  label: string
  value: number | string
  icon?: Component
  tone?: Tone
  to?: RouteLocationRaw
}>()
</script>

<template>
  <component :is="to ? 'RouterLink' : 'div'" :to="to" class="stat" :data-tone="tone ?? 'default'">
    <div class="head">
      <span class="eyebrow">{{ label }}</span>
      <component :is="icon" v-if="icon" :size="15" class="icon" />
    </div>
    <div class="value mono">{{ value }}</div>
  </component>
</template>

<style scoped>
.stat {
  --tone: var(--ar-text);
  position: relative;
  display: block;
  padding: 12px 14px 14px;
  background: var(--ar-surface);
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  color: inherit;
  text-decoration: none;
  overflow: hidden;
  transition: border-color 0.15s;
}
.stat::before {
  content: '';
  position: absolute;
  inset: 0 auto 0 0;
  width: 3px;
  background: var(--tone);
  opacity: 0.85;
}
a.stat:hover {
  border-color: var(--ar-border-strong);
  text-decoration: none;
}
.head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.icon {
  color: var(--ar-text-subtle);
}
.value {
  margin-top: 6px;
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.03em;
  color: var(--tone);
}
[data-tone='default'] {
  --tone: var(--ar-text);
}
[data-tone='info'] {
  --tone: var(--ar-info);
}
[data-tone='success'] {
  --tone: var(--ar-success);
}
[data-tone='warning'] {
  --tone: var(--ar-warning);
}
[data-tone='error'] {
  --tone: var(--ar-error);
}
[data-tone='primary'] {
  --tone: var(--ar-primary);
}
</style>
