<script setup lang="ts">
import { MessageSquarePlus, Plus } from '@lucide/vue'
import { NButton, NInput } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

/** "Something else": a free-text request for things that are not in the catalog. */
defineProps<{ title: string; hint?: string; placeholder: string }>()
const emit = defineEmits<{ add: [text: string] }>()
const { t } = useI18n()
const text = ref('')

function add() {
  const value = text.value.trim()
  if (!value) return
  emit('add', value)
  text.value = ''
}
</script>

<template>
  <div class="free-text">
    <div class="head">
      <MessageSquarePlus :size="15" />
      <span class="title">{{ title }}</span>
      <small v-if="hint" class="muted">· {{ hint }}</small>
    </div>
    <div class="row">
      <NInput
        v-model:value="text"
        size="small"
        :placeholder="placeholder"
        maxlength="255"
        @keydown.enter.prevent="add"
      />
      <NButton size="small" secondary :disabled="!text.trim()" @click="add">
        <template #icon><Plus :size="14" /></template>
        {{ t('common.add') }}
      </NButton>
    </div>
  </div>
</template>

<style scoped>
.free-text {
  display: grid;
  gap: 8px;
  padding: 10px 12px;
  border: 1px dashed var(--ar-border-strong);
  border-radius: 3px;
}
.head {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--ar-text-muted);
}
.title {
  font-weight: 500;
  color: var(--ar-text);
}
.row :deep(.n-input) {
  flex: 1;
}
</style>
