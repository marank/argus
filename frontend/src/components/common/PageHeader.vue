<script setup lang="ts">
import { ArrowLeft } from '@lucide/vue'
import { useRouter, type RouteLocationRaw } from 'vue-router'

const props = defineProps<{
  title: string
  subtitle?: string
  eyebrow?: string
  /**
   * Link back to the overview, e.g. the list a record page was opened from. Coming from
   * that list, it goes back in the history, so the list shows as it was left.
   */
  back?: { label: string; to: RouteLocationRaw }
}>()
const router = useRouter()

function goBack() {
  const target = router.resolve(props.back!.to).path
  const previous = (window.history.state as { back?: string } | null)?.back
  if (previous && previous.split('?')[0] === target) router.back()
  else router.push(props.back!.to)
}
</script>

<template>
  <header class="page-header">
    <div class="titles">
      <a v-if="back" :href="router.resolve(back.to).href" class="back" @click.prevent="goBack">
        <ArrowLeft :size="13" />
        {{ back.label }}
      </a>
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
.back {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  margin-bottom: 8px;
  color: var(--ar-text-muted);
  font-size: 12px;
  text-decoration: none;
}
.back:hover,
.back:focus-visible {
  color: var(--ar-primary);
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
