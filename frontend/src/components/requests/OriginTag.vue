<script setup lang="ts">
import { ScanLine } from '@lucide/vue'
import { useI18n } from 'vue-i18n'

import type { AssetRequestListItem } from '@/types/requests'

/** Marks a direct hand-out next to the status; a request needs no mark. */
defineProps<{ origin: AssetRequestListItem['origin'] }>()
const { t } = useI18n()
</script>

<template>
  <span v-if="origin === 'direct'" class="origin-tag">
    <ScanLine :size="13" :stroke-width="2" />
    {{ t('requests.direct.title') }}
  </span>
</template>

<style scoped>
.origin-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 1px 8px;
  border: 1px solid color-mix(in srgb, var(--ar-violet) 35%, transparent);
  border-radius: 3px;
  background: color-mix(in srgb, var(--ar-violet) 10%, transparent);
  color: var(--ar-violet);
  font-size: 12px;
  font-weight: 600;
  line-height: 20px;
  vertical-align: middle;
}
</style>
