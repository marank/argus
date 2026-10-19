<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

/**
 * Touch/pen/mouse signature field. Draws black ink on white so the exported PNG
 * reads well on paper and in dark mode.
 */
const emit = defineEmits<{ change: [empty: boolean] }>()

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
  <div class="pad">
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
  </div>
</template>

<style scoped>
.pad {
  position: relative;
  height: 220px;
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
.cross {
  position: absolute;
  left: 18px;
  bottom: 50px;
  color: #9aa6b2;
  font-size: 16px;
  pointer-events: none;
}
</style>
