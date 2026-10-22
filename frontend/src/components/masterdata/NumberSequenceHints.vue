<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { categoriesApi, numberSequencesApi } from '@/api/masterdata'
import type { Category, NumberSequence } from '@/types/masterdata'

/**
 * Number sequences worth picking for a record's `number_sequence`: the sequence of the category
 * in the form field `from` (a category's parent, a model's category) and the general asset
 * sequence, each with its next number. A click fills the field.
 */
const props = defineProps<{
  form: Record<string, unknown>
  from: 'parent' | 'category'
  readonly?: boolean
}>()
const emit = defineEmits<{ set: [key: string, value: unknown] }>()
const { t } = useI18n()

const general = ref<NumberSequence | null>(null)
const source = ref<{ category: Category; sequence: NumberSequence } | null>(null)

onMounted(async () => {
  const page = await numberSequencesApi.list({ q: 'asset', page_size: 30 })
  general.value = page.items.find((s) => s.code === 'asset') ?? null
})

watch(
  () => props.form[props.from] as string | null,
  async (id) => {
    source.value = null
    if (!id) return
    const category = await categoriesApi.get(id)
    if (!category.number_sequence || props.form[props.from] !== id) return
    const sequence = await numberSequencesApi.get(category.number_sequence.id)
    if (props.form[props.from] === id) source.value = { category, sequence }
  },
  { immediate: true },
)

const hints = computed(() => [
  ...(source.value
    ? [
        {
          label: t(`masterdata.fields.${props.from}Sequence`, { name: source.value.category.name }),
          sequence: source.value.sequence,
        },
      ]
    : []),
  ...(general.value
    ? [{ label: t('masterdata.fields.generalSequence'), sequence: general.value }]
    : []),
])

function pick(sequence: NumberSequence) {
  if (!props.readonly) emit('set', 'number_sequence', sequence.id)
}
</script>

<template>
  <div v-if="hints.length" class="hints">
    <button
      v-for="hint in hints"
      :key="hint.sequence.id"
      type="button"
      class="hint"
      :class="{ active: form.number_sequence === hint.sequence.id }"
      :disabled="readonly"
      :title="t('masterdata.fields.useSequence')"
      @click="pick(hint.sequence)"
    >
      <span class="eyebrow">{{ hint.label }}</span>
      <span>{{ hint.sequence.name }}</span>
      <span class="muted">{{ t('masterdata.fields.nextNumber') }}</span>
      <code class="mono">{{ hint.sequence.preview }}</code>
    </button>
  </div>
</template>

<style scoped>
.hints {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 4px;
}
.hint {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 10px;
  padding: 8px 12px;
  border: 1px dashed var(--ar-border-strong);
  border-radius: 3px;
  background: var(--ar-surface-sunken);
  color: inherit;
  font: inherit;
  text-align: left;
  cursor: pointer;
}
.hint:hover:not(:disabled),
.hint.active {
  border-style: solid;
  border-color: var(--ar-primary);
}
.hint:disabled {
  cursor: default;
}
code {
  padding: 1px 6px;
  border-radius: 2px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
  font-weight: 600;
}
</style>
