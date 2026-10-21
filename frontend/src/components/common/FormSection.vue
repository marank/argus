<script setup lang="ts">
/** A titled card grouping the fields of a form; the content is a column (inputs, toggle rows). */
defineProps<{ title?: string }>()
</script>

<template>
  <section class="form-section">
    <div v-if="title" class="eyebrow title">{{ title }}</div>
    <div class="body"><slot /></div>
  </section>
</template>

<style scoped>
.form-section {
  padding: 14px 16px;
  background: var(--ar-surface);
  border: 1px solid var(--ar-border);
  border-radius: 4px;
}
.form-section + .form-section {
  margin-top: 12px;
}
.title {
  margin-bottom: 12px;
}
.body {
  display: flex;
  flex-direction: column;
}
</style>
