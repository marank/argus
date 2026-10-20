<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core'
import { NCard, NInput } from 'naive-ui'
import { ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import type { WidgetProps } from '@/types/dashboard'

/** A personal notepad; the text is kept with the user's dashboard layout. */
const props = defineProps<WidgetProps>()
const emit = defineEmits<{ 'update:options': [options: Record<string, unknown>] }>()

const MAX_LENGTH = 4000

const { t } = useI18n()
const stored = () => (typeof props.options.text === 'string' ? props.options.text : '')
const text = ref(stored())
const saved = ref(true)

// Another tab or the editor may change it; the field follows unless something is being typed.
watch(stored, (value) => {
  if (saved.value) text.value = value
})

const save = useDebounceFn(() => {
  emit('update:options', { ...props.options, text: text.value })
  saved.value = true
}, 800)

function onInput(value: string) {
  text.value = value
  saved.value = false
  save()
}
</script>

<template>
  <NCard :title="t('dashboard.widgets.notes.title')" size="small">
    <template #header-extra>
      <span class="muted status">{{
        saved ? t('dashboard.widgets.notes.saved') : t('dashboard.widgets.notes.saving')
      }}</span>
    </template>
    <NInput
      :value="text"
      type="textarea"
      :maxlength="MAX_LENGTH"
      :autosize="{ minRows: 4, maxRows: 14 }"
      :placeholder="t('dashboard.widgets.notes.placeholder')"
      @update:value="onInput"
    />
  </NCard>
</template>

<style scoped>
.status {
  font-size: 12px;
}
</style>
