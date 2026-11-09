<script setup lang="ts">
import { NPopover, useMessage, useThemeVars } from 'naive-ui'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import { errorPopover, hideError, showError } from '@/composables/useErrorPopover'

/**
 * The red popover of `showError`, pointing at the element the error is about. It follows that
 * element while scrolling and closes on a click elsewhere, a key press or after a while; at a
 * refused form field it stays until the value changes instead. Hovering or focusing a refused
 * field shows that field's error.
 */
const message = useMessage()
const vars = useThemeVars()

const HIDE_AFTER_MS = 8000

const visible = ref(false)
const x = ref(0)
const y = ref(0)
const below = ref(true)
let frame = 0
let timer: ReturnType<typeof setTimeout> | undefined
let observer: MutationObserver | null = null

const isField = (el: HTMLElement) => el.dataset.fieldError !== undefined
/** A form field points at its input, not at its label. */
const target = (el: HTMLElement) =>
  isField(el) ? (el.querySelector<HTMLElement>('.n-form-item-blank, .n-switch') ?? el) : el

function place(): boolean {
  const anchor = errorPopover.anchor
  if (!anchor?.isConnected) return false
  const rect = target(anchor).getBoundingClientRect()
  below.value = window.innerHeight - rect.bottom > 96 || rect.top < 96
  x.value = rect.left + Math.min(20, rect.width / 2)
  y.value = below.value ? rect.bottom : rect.top
  return true
}

function follow() {
  if (!place()) return hideError()
  frame = requestAnimationFrame(follow)
}

function stop() {
  visible.value = false
  cancelAnimationFrame(frame)
  clearTimeout(timer)
  observer?.disconnect()
  observer = null
}

watch(
  () => errorPopover.serial,
  () => {
    stop()
    const anchor = errorPopover.anchor
    if (!errorPopover.message) return
    if (!anchor) {
      message.error(errorPopover.message, { duration: 6000 })
      return hideError()
    }
    if (isField(anchor)) {
      // Gone or changed together with the field's error.
      observer = new MutationObserver(() => {
        if (anchor.dataset.fieldError) errorPopover.message = anchor.dataset.fieldError
        else hideError()
      })
      observer.observe(anchor, { attributes: true, attributeFilter: ['data-field-error'] })
    } else {
      timer = setTimeout(hideError, HIDE_AFTER_MS)
    }
    visible.value = true
    follow()
  },
)
watch(
  () => errorPopover.message,
  (text) => {
    if (!text) stop()
  },
)

function onPointerDown(event: Event) {
  const anchor = errorPopover.anchor
  if (visible.value && anchor && !anchor.contains(event.target as Node)) hideError()
}
function onKeyDown() {
  const anchor = errorPopover.anchor
  if (visible.value && anchor && !isField(anchor)) hideError()
}
/** Hovering or focusing a refused field shows its error. */
function onEnter(event: Event) {
  const field = (event.target as Element | null)?.closest?.<HTMLElement>('[data-field-error]')
  if (field && field !== errorPopover.anchor) showError(field.dataset.fieldError ?? '', field)
}

onMounted(() => {
  document.addEventListener('pointerdown', onPointerDown, true)
  document.addEventListener('keydown', onKeyDown, true)
  document.addEventListener('mouseover', onEnter)
  document.addEventListener('focusin', onEnter)
})
onBeforeUnmount(() => {
  stop()
  document.removeEventListener('pointerdown', onPointerDown, true)
  document.removeEventListener('keydown', onKeyDown, true)
  document.removeEventListener('mouseover', onEnter)
  document.removeEventListener('focusin', onEnter)
})

const overrides = computed(() => ({ color: vars.value.errorColor, textColor: '#fff' }))
</script>

<template>
  <NPopover
    :show="visible"
    :x="x"
    :y="y"
    trigger="manual"
    :placement="below ? 'bottom-start' : 'top-start'"
    arrow-point-to-center
    :theme-overrides="overrides"
    :style="{ maxWidth: '340px' }"
  >
    <span class="error-popover" role="alert">{{ errorPopover.message }}</span>
  </NPopover>
</template>

<style scoped>
.error-popover {
  font-size: 13px;
  line-height: 1.45;
}
</style>
