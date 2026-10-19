<script setup lang="ts">
defineProps<{ title: string; subtitle?: string; eyebrow?: string }>()
</script>

<template>
  <header class="page-header">
    <div class="titles">
      <div v-if="eyebrow || $slots.eyebrow" class="eyebrow">
        <slot name="eyebrow">{{ eyebrow }}</slot>
      </div>
      <h1>
        {{ title }}
        <slot name="badge" />
      </h1>
      <p v-if="subtitle" class="muted">{{ subtitle }}</p>
    </div>
    <div v-if="$slots.actions" class="actions">
      <slot name="actions" />
    </div>
  </header>
</template>

<style scoped>
.page-header {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px 24px;
  padding-bottom: 16px;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--ar-border);
}
h1 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 2px 0 0;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.015em;
}
p {
  margin: 4px 0 0;
  max-width: 70ch;
}
.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
</style>
