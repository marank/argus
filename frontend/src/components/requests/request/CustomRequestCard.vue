<script setup lang="ts">
import { MessageSquarePlus, Plus } from '@lucide/vue'
import { NButton, NInput } from 'naive-ui'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

/** Separate card for requests that fit no device group at all. */
const props = defineProps<{ initial?: string }>()
const emit = defineEmits<{ add: [text: string] }>()
const { t } = useI18n()
const text = ref(props.initial ?? '')

function add() {
  const value = text.value.trim()
  if (!value) return
  emit('add', value)
  text.value = ''
}
</script>

<template>
  <section class="custom">
    <header>
      <span class="icon"><MessageSquarePlus :size="20" :stroke-width="1.5" /></span>
      <div>
        <h2>{{ t('requests.new.notFound') }}</h2>
        <p class="muted">{{ t('requests.new.notFoundHint') }}</p>
      </div>
    </header>
    <div class="row">
      <NInput
        v-model:value="text"
        :placeholder="t('requests.new.notFoundPlaceholder')"
        maxlength="255"
        @keydown.enter.prevent="add"
      />
      <NButton secondary :disabled="!text.trim()" @click="add">
        <template #icon><Plus :size="14" /></template>
        {{ t('common.add') }}
      </NButton>
    </div>
  </section>
</template>

<style scoped>
.custom {
  display: grid;
  gap: 14px;
  padding: 18px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
}
header {
  display: flex;
  align-items: center;
  gap: 12px;
}
.icon {
  display: grid;
  place-items: center;
  width: 40px;
  height: 40px;
  border-radius: 3px;
  background: var(--ar-surface-sunken);
  color: var(--ar-text-muted);
}
h2 {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
}
header p {
  margin: 2px 0 0;
}
.row :deep(.n-input) {
  flex: 1;
}
</style>
