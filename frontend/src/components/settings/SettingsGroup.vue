<script setup lang="ts">
/** One block of a settings page: title and explanation on the left, the fields on the right. */
defineProps<{ title: string; description?: string }>()
</script>

<template>
  <section class="settings-group">
    <header>
      <h2>{{ title }}</h2>
      <p v-if="description" class="muted">{{ description }}</p>
    </header>
    <div class="body">
      <slot />
    </div>
  </section>
</template>

<style scoped>
.settings-group {
  display: grid;
  grid-template-columns: minmax(180px, 260px) minmax(0, 1fr);
  gap: 12px 32px;
  padding: 22px 0;
  border-top: 1px solid var(--ar-border);
}
.settings-group:first-child {
  border-top: none;
  padding-top: 4px;
}
h2 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}
p {
  margin: 6px 0 0;
  font-size: 12.5px;
  line-height: 1.5;
}
.body {
  min-width: 0;
  container-type: inline-size;
  padding: 4px 18px;
  background: var(--ar-surface);
  border: 1px solid var(--ar-border);
  border-radius: 3px;
}
@container (max-width: 820px) {
  .settings-group {
    grid-template-columns: minmax(0, 1fr);
  }
}
</style>
