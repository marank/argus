<script setup lang="ts">
import { RotateCcw } from '@lucide/vue'
import { onBeforeUnmount, onMounted, ref } from 'vue'
import { useI18n } from 'vue-i18n'

/**
 * Touch/pen/mouse signature field. Draws black ink on white so the exported PNG
 * reads well on paper and in dark mode.
 */
const props = withDefaults(defineProps<{ height?: number }>(), { height: 220 })
const emit = defineEmits<{ change: [empty: boolean] }>()
const { t } = useI18n()

const canvas = ref<HTMLCanvasElement | null>(null)
const empty = ref(true)
let ctx: CanvasRenderingContext2D | null = null
let drawing = false
let last: { x: number; y: number } | null = null

function setup() {
  const el = canvas.value
  if (!el) return
  const ratio = window.devicePixelRatio || 1
  const { width, height } = el.getBoundingClientRect()
  el.width = Math.round(width * ratio)
  el.height = Math.round(height * ratio)
  ctx = el.getContext('2d')
  if (!ctx) return
  ctx.scale(ratio, ratio)
  ctx.lineCap = 'round'
  ctx.lineJoin = 'round'
  ctx.strokeStyle = '#0b1220'
  clear()
}

function point(event: PointerEvent) {
  const rect = canvas.value!.getBoundingClientRect()
  return { x: event.clientX - rect.left, y: event.clientY - rect.top }
}

function start(event: PointerEvent) {
  event.preventDefault()
  canvas.value?.setPointerCapture(event.pointerId)
  drawing = true
  last = point(event)
  // A tap leaves a dot.
  draw(event)
}

function draw(event: PointerEvent) {
  if (!drawing || !ctx || !last) return
  const p = point(event)
  ctx.lineWidth = event.pointerType === 'pen' ? 1.5 + event.pressure * 2.5 : 2.6
  ctx.beginPath()
  ctx.moveTo(last.x, last.y)
  ctx.lineTo(p.x + 0.01, p.y + 0.01)
  ctx.stroke()
  last = p
  if (empty.value) {
    empty.value = false
    emit('change', false)
  }
}

function end() {
  drawing = false
  last = null
}

function clear() {
  if (!ctx || !canvas.value) return
  ctx.save()
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.fillStyle = '#ffffff'
  ctx.fillRect(0, 0, canvas.value.width, canvas.value.height)
  ctx.restore()
  empty.value = true
  emit('change', true)
}

function toDataUrl(): string {
  return canvas.value?.toDataURL('image/png') ?? ''
}

onMounted(() => {
  setup()
  window.addEventListener('resize', setup)
})
onBeforeUnmount(() => window.removeEventListener('resize', setup))

defineExpose({ clear, toDataUrl, isEmpty: () => empty.value })
</script>

<template>
  <div class="pad" :style="{ height: `${props.height}px` }">
    <canvas
      ref="canvas"
      @pointerdown="start"
      @pointermove="draw"
      @pointerup="end"
      @pointercancel="end"
      @pointerleave="end"
    />
    <div class="baseline" />
    <span class="cross">✕</span>
    <span v-if="empty" class="placeholder">{{ t('terminal.signHere') }}</span>
    <button v-else type="button" class="clear" @click="clear">
      <RotateCcw :size="18" /> {{ t('terminal.clear') }}
    </button>
  </div>
</template>

<style scoped>
.pad {
  position: relative;
  border: 1px solid var(--ar-border-strong);
  border-radius: 4px;
  overflow: hidden;
  background: #fff;
}
canvas {
  display: block;
  width: 100%;
  height: 100%;
  touch-action: none;
  cursor: crosshair;
}
.baseline {
  position: absolute;
  left: 40px;
  right: 24px;
  bottom: 52px;
  border-bottom: 1px dashed #9aa6b2;
  pointer-events: none;
}
.placeholder {
  position: absolute;
  inset: 0 0 52px;
  display: grid;
  place-items: center;
  color: #9aa6b2;
  font-size: 22px;
  pointer-events: none;
}
/* Light colors on purpose: the pad stays white in dark mode. */
.clear {
  position: absolute;
  top: 12px;
  right: 12px;
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 48px;
  padding: 0 18px;
  border: 1px solid #c8d0d8;
  border-radius: 4px;
  background: #f4f6f8;
  color: #334155;
  font: inherit;
  font-size: 16px;
  cursor: pointer;
}
.cross {
  position: absolute;
  left: 18px;
  bottom: 50px;
  color: #9aa6b2;
  font-size: 16px;
  pointer-events: none;
}
</style>
