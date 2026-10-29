<script setup lang="ts">
// The Argus mark ("Schnittmenge") on its teal tile. Fixed brand colours, the same in
// light and dark; the favicon is the tile-less variant (public/favicon.svg).
defineProps<{ size: number }>()
</script>

<template>
  <svg viewBox="0 0 32 32" :width="size" :height="size" aria-hidden="true" class="mark">
    <rect width="32" height="32" rx="7" fill="#0e7490" />
    <rect x="12" y="12" width="8" height="8" fill="#fff" fill-opacity=".55" />
    <g fill="none" stroke="#fff" stroke-width="2">
      <rect x="7" y="7" width="13" height="13" rx="1" />
      <rect x="12" y="12" width="13" height="13" rx="1" />
    </g>
  </svg>
</template>

<style scoped>
.mark {
  flex-shrink: 0;
}
</style>
