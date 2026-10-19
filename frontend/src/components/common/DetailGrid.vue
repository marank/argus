<script setup lang="ts">
export interface DetailEntry {
  label: string
  value?: string | number | null
  mono?: boolean
  /** Name of a slot to render instead of `value`. */
  slot?: string
  wide?: boolean
}

defineProps<{ entries: DetailEntry[] }>()
</script>

<template>
  <dl class="detail-grid">
    <div v-for="entry in entries" :key="entry.label" class="entry" :class="{ wide: entry.wide }">
      <dt class="eyebrow">{{ entry.label }}</dt>
      <dd :class="{ mono: entry.mono }">
        <slot v-if="entry.slot" :name="entry.slot" />
        <template v-else>{{
          entry.value === null || entry.value === undefined || entry.value === ''
            ? '—'
            : entry.value
        }}</template>
      </dd>
    </div>
  </dl>
</template>

<style scoped>
.detail-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 14px 20px;
  margin: 0;
}
.entry.wide {
  grid-column: 1 / -1;
}
dt {
  margin-bottom: 3px;
}
dd {
  margin: 0;
  overflow-wrap: anywhere;
  white-space: pre-line;
}
</style>
