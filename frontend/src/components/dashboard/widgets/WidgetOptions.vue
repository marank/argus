<script setup lang="ts">
import { Settings2 } from '@lucide/vue'
import { NButton, NPopover } from 'naive-ui'
import { useI18n } from 'vue-i18n'

/** The gear in a widget's header with its quick settings; the settings go in the slot. */
const { t } = useI18n()
</script>

<template>
  <NPopover trigger="click" placement="bottom-end" scrollable style="max-height: 360px">
    <template #trigger>
      <NButton quaternary size="tiny" :title="t('dashboard.widgets.settings')">
        <template #icon><Settings2 /></template>
      </NButton>
    </template>
    <div class="widget-options">
      <slot />
    </div>
  </NPopover>
</template>

<style scoped>
.widget-options {
  display: grid;
  gap: 10px;
  padding: 4px 2px;
  min-width: 180px;
}
.widget-options :deep(.eyebrow) {
  display: block;
  margin-bottom: 4px;
}
</style>
