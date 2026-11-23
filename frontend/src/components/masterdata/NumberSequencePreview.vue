<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { watchDebounced } from '@vueuse/core'
import { ref } from 'vue'
import { useI18n } from 'vue-i18n'

import { numberSequencesApi } from '@/api/masterdata'
import { ApiError } from '@/api/client'

/** Live preview of the next numbers while the pattern is being edited. */
const props = defineProps<{
  form: Partial<Schemas['NumberSequenceOut']>
  // eslint-disable-next-line vue/no-unused-properties -- every extra section of CrudFormDrawer gets form, row and readonly
  row?: Schemas['NumberSequenceOut'] | null
}>()
const { t } = useI18n()

const examples = ref<string[]>([])
const error = ref('')

watchDebounced(
  () => [props.form.prefix, props.form.pattern, props.form.padding, props.form.next_value],
  async () => {
    try {
      examples.value = (
        await numberSequencesApi.preview({ code: 'preview', name: 'preview', ...props.form })
      ).examples
      error.value = ''
    } catch (e) {
      examples.value = []
      error.value = e instanceof ApiError ? e.message : String(e)
    }
  },
  { debounce: 250, immediate: true },
)
</script>

<template>
  <div class="preview" :class="{ invalid: error }">
    <span class="eyebrow">{{ t('masterdata.fields.preview') }}</span>
    <span v-if="error" class="error">{{ error }}</span>
    <span v-else class="examples">
      <code v-for="example in examples" :key="example" class="mono">{{ example }}</code>
      <span class="muted">…</span>
    </span>
  </div>
</template>

<style scoped>
.preview {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 14px;
  margin-top: 4px;
  padding: 10px 12px;
  border: 1px dashed var(--ar-border-strong);
  border-radius: 3px;
  background: var(--ar-surface-sunken);
}
.examples {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
code {
  padding: 1px 6px;
  border-radius: 2px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
  font-weight: 600;
}
.invalid {
  border-color: var(--ar-error);
}
.error {
  color: var(--ar-error);
  font-size: 12px;
}
</style>
