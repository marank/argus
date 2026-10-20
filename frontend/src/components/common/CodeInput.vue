<script setup lang="ts">
import { computed, ref, watch } from 'vue'

/**
 * One-time code as single digit boxes. Typing moves on, Backspace moves back,
 * pasting or autofill (`one-time-code`) spreads the digits over the boxes.
 * Emits `complete` once all boxes are filled.
 */
const props = withDefaults(defineProps<{ length?: number; disabled?: boolean; label?: string }>(), {
  length: 6,
  disabled: false,
  label: '',
})
const code = defineModel<string>({ required: true })
const emit = defineEmits<{ complete: [code: string] }>()

/**
 * The code as typed so far. The model only changes once the parent re-renders;
 * moving between boxes needs the new value right away.
 */
const value = ref(code.value)
watch(code, (outer) => (value.value = outer))
function set(next: string) {
  value.value = code.value = next
}

const boxes = ref<HTMLInputElement[]>([])
const digits = computed(() => Array.from({ length: props.length }, (_, i) => value.value.charAt(i)))

function focus(index = Math.min(value.value.length, props.length - 1)) {
  const box = boxes.value[Math.max(0, Math.min(index, props.length - 1))]
  box?.focus()
  box?.select()
}

/** Writes `text` (digits only) into the boxes from `index` on. */
function fill(index: number, text: string) {
  const incoming = text.replace(/\D/g, '')
  if (!incoming) return
  const chars = digits.value.slice()
  // A whole code (paste, autofill) always starts at the first box.
  const start = incoming.length >= props.length ? 0 : index
  for (const [offset, char] of [...incoming].entries()) {
    if (start + offset >= props.length) break
    chars[start + offset] = char
  }
  // Keep the code contiguous: stop at the first empty box.
  const end = chars.findIndex((c) => !c)
  set(chars.slice(0, end === -1 ? props.length : end).join(''))
  focus(Math.min(start + incoming.length, props.length - 1))
  if (value.value.length === props.length) emit('complete', value.value)
}

function onInput(index: number, event: Event) {
  const input = event.target as HTMLInputElement
  // Only what was typed or inserted, not the digit already in the box; autofill brings no `data`.
  const text = (event as InputEvent).data ?? input.value
  input.value = digits.value[index] ?? ''
  fill(index, text)
}

function onKeydown(index: number, event: KeyboardEvent) {
  if (event.key === 'Backspace') {
    event.preventDefault()
    const at = digits.value[index] ? index : index - 1
    if (at < 0) return
    set(value.value.slice(0, at))
    focus(at)
  } else if (event.key === 'ArrowLeft') {
    event.preventDefault()
    focus(index - 1)
  } else if (event.key === 'ArrowRight') {
    event.preventDefault()
    focus(Math.min(index + 1, value.value.length))
  }
}

function onPaste(index: number, event: ClipboardEvent) {
  event.preventDefault()
  fill(index, event.clipboardData?.getData('text') ?? '')
}

/** Clicking a box after the typed digits lands on the next free one. */
function onFocus(index: number) {
  if (index > value.value.length) focus(value.value.length)
  else boxes.value[index]?.select()
}

defineExpose({ focus })
</script>

<template>
  <div class="code-input" role="group" :aria-label="label">
    <input
      v-for="(digit, index) in digits"
      :key="index"
      :ref="(el) => (boxes[index] = el as HTMLInputElement)"
      :value="digit"
      class="box mono"
      type="text"
      inputmode="numeric"
      pattern="[0-9]*"
      :autocomplete="index === 0 ? 'one-time-code' : 'off'"
      :aria-label="`${label} ${index + 1}/${length}`"
      :disabled="disabled"
      @input="onInput(index, $event)"
      @keydown="onKeydown(index, $event)"
      @paste="onPaste(index, $event)"
      @focus="onFocus(index)"
    />
  </div>
</template>

<style scoped>
.code-input {
  display: grid;
  grid-template-columns: repeat(v-bind(length), minmax(0, 1fr));
  gap: 8px;
  width: 100%;
}
.box {
  width: 100%;
  min-width: 0;
  height: 46px;
  padding: 0;
  font-size: 20px;
  font-weight: 600;
  text-align: center;
  color: var(--ar-text);
  caret-color: var(--ar-primary);
  background: var(--ar-bg);
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  outline: none;
  transition:
    border-color 0.15s,
    box-shadow 0.15s;
}
.box:hover:not(:disabled) {
  border-color: var(--ar-primary);
}
.box:focus {
  border-color: var(--ar-primary);
  box-shadow: 0 0 0 2px var(--ar-primary-soft);
}
.box:disabled {
  opacity: 0.6;
}
</style>
