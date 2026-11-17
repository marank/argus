<script setup lang="ts">
import { useDebounceFn } from '@vueuse/core'
import { ScanLine } from '@lucide/vue'
import { NAutoComplete } from 'naive-ui'
import { ref, type VNodeChild } from 'vue'

/**
 * Scan field with suggestions: typing searches after a short pause and lists the hits,
 * a click picks one. The hits close on Enter and reopen with the next keystroke. Enter picks a hit chosen with the arrow keys, else hands over the
 * typed or scanned code as is.
 */
const props = defineProps<{
  options: { value: string; label: string }[]
  placeholder?: string
  loading?: boolean
  /** Shown when nothing matches; without it an empty list stays closed. */
  emptyText?: string
  /** Draws a hit richer than its label (the label stays its text for screen readers). */
  renderLabel?: (option: { value?: string | number; label?: string }) => VNodeChild
}>()
const emit = defineEmits<{ search: [q: string]; select: [value: string]; enter: [code: string] }>()
const code = defineModel<string>({ default: '' })

const search = useDebounceFn((q: string) => emit('search', q), 250)

/** Whether an option was chosen with the arrow keys since the last keystroke. */
const arrowed = ref(false)
/**
 * The hits only open while typing: not on focus, and not after Enter handed over the
 * code, so they never cover the list below while that code is being processed.
 */
const typing = ref(false)

/** Naive clears to null after an option was picked. */
function onInput(value: string | null) {
  code.value = value ?? ''
  arrowed.value = false
  typing.value = Boolean(code.value.trim())
  search(code.value.trim())
}

/**
 * Naive would pick whatever option is highlighted on Enter, also one only hovered
 * or left over from an earlier search. A scan arrives faster than its results, so
 * Enter takes the typed code unless an option was chosen with the arrow keys.
 */
function onKeydown(event: KeyboardEvent) {
  if (event.key === 'ArrowDown' || event.key === 'ArrowUp') arrowed.value = true
  if (event.key !== 'Enter' || event.isComposing || arrowed.value) return
  event.preventDefault()
  event.stopPropagation()
  typing.value = false
  const typed = code.value.trim()
  if (typed) emit('enter', typed)
}
</script>

<template>
  <!-- Capture phase: decide about Enter before Naive's own handler sees it. -->
  <div class="scan-combobox" @keydown.capture="onKeydown">
    <NAutoComplete
      :value="code"
      size="medium"
      :options="props.options"
      :placeholder="placeholder"
      :loading="loading"
      :get-show="() => typing"
      :show-empty="Boolean(emptyText)"
      clear-after-select
      :render-label="props.renderLabel as never"
      @update:value="onInput"
      @select="(value: string | number) => emit('select', String(value))"
    >
      <template #prefix><ScanLine :size="16" /></template>
      <template #empty
        ><span class="muted empty">{{ emptyText }}</span></template
      >
    </NAutoComplete>
  </div>
</template>

<style scoped>
.scan-combobox :deep(input) {
  font-family: var(--ar-font-mono);
}
.empty {
  font-size: 11.5px;
}
</style>
