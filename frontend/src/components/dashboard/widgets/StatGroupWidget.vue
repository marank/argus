<script setup lang="ts">
import type { Schemas } from '@/api/types'
import { ArrowLeft, ArrowRight, Eye, EyeOff } from '@lucide/vue'
import { computed, ref } from 'vue'
import { useI18n } from 'vue-i18n'

import StatCard from '@/components/common/StatCard.vue'
import StatGroup from '@/components/dashboard/StatGroup.vue'
import {
  availableCards,
  mergeOrder,
  moveBefore,
  orderCards,
  type StatCardDef,
  type WidgetDef,
} from '@/components/dashboard/widgets'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'

/**
 * A panel of key figures. While editing, every card can be dragged within the
 * panel, moved with the arrows and hidden.
 */
const props = defineProps<{
  def: WidgetDef
  data: Schemas['ITOverviewOut']
  hiddenCards: string[]
  cardOrder: string[]
  editing?: boolean
}>()
const emit = defineEmits<{ toggleCard: [key: string]; reorder: [order: string[]] }>()

const { t } = useI18n()
const features = useFeaturesStore()
const auth = useAuthStore()

const isHidden = (card: StatCardDef) => props.hiddenCards.includes(card.key)
const cards = computed(() =>
  orderCards(availableCards(props.def, features.isOn, auth.can), props.cardOrder).filter(
    (card) => props.editing || !isHidden(card),
  ),
)
const label = (card: StatCardDef) => t(card.label, card.labelArgs?.(features.rules) ?? {})

/** Reorders among all cards, so those of switched-off modules keep their place. */
function moveTo(key: string, target: string) {
  const all = mergeOrder(
    (props.def.cards ?? []).map((c) => c.key),
    props.cardOrder,
  )
  emit('reorder', moveBefore(all, key, target))
}

function move(index: number, delta: number) {
  const neighbour = cards.value[index + delta]
  if (neighbour) moveTo(cards.value[index]!.key, neighbour.key)
}

/* Drag and drop stays inside the panel; the events do not reach the widget around it. */
const dragged = ref<string | null>(null)
let lastOver: string | null = null

function onDragStart(event: DragEvent, card: StatCardDef) {
  event.stopPropagation()
  dragged.value = card.key
  lastOver = card.key
  event.dataTransfer?.setData('text/plain', card.key)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDragOver(event: DragEvent, card: StatCardDef) {
  if (!dragged.value) return
  event.preventDefault()
  event.stopPropagation()
  if (card.key !== lastOver && card.key !== dragged.value) moveTo(dragged.value, card.key)
  lastOver = card.key
}

function onDragEnd(event: DragEvent) {
  event.stopPropagation()
  dragged.value = null
  lastOver = null
}
</script>

<template>
  <StatGroup :title="t(def.title)" :icon="def.icon" :count="cards.length">
    <template v-for="(card, index) in cards" :key="card.key">
      <!-- eslint-disable-next-line vuejs-accessibility/no-static-element-interactions -- dragging is the mouse shortcut; the move buttons below do the same by keyboard -->
      <div
        v-if="editing"
        class="card-edit"
        :class="{ off: isHidden(card), dragged: dragged === card.key }"
        draggable="true"
        @dragstart="onDragStart($event, card)"
        @dragover="onDragOver($event, card)"
        @drop.prevent.stop
        @dragend="onDragEnd"
      >
        <StatCard
          :label="label(card)"
          :value="card.value(data)"
          :icon="card.icon"
          :tone="card.tone?.(data)"
        />
        <div class="card-tools">
          <button
            type="button"
            :disabled="index === 0"
            :title="t('dashboard.edit.moveUp')"
            @click="move(index, -1)"
          >
            <ArrowLeft :size="14" />
          </button>
          <button
            type="button"
            :disabled="index === cards.length - 1"
            :title="t('dashboard.edit.moveDown')"
            @click="move(index, 1)"
          >
            <ArrowRight :size="14" />
          </button>
          <button
            type="button"
            :aria-pressed="!isHidden(card)"
            :title="isHidden(card) ? t('dashboard.edit.show') : t('dashboard.edit.hide')"
            @click="emit('toggleCard', card.key)"
          >
            <component :is="isHidden(card) ? EyeOff : Eye" :size="14" />
          </button>
        </div>
      </div>
      <StatCard
        v-else
        :label="label(card)"
        :value="card.value(data)"
        :icon="card.icon"
        :tone="card.tone?.(data)"
        :alert="card.alert?.(data)"
        :to="card.to"
      />
    </template>
  </StatGroup>
</template>

<style scoped>
.card-edit {
  position: relative;
  padding-bottom: 32px;
  cursor: grab;
}
.card-edit:active {
  cursor: grabbing;
}
.card-edit.dragged {
  opacity: 0.4;
}
.card-edit.off :deep(.stat) {
  opacity: 0.35;
}
.card-tools {
  position: absolute;
  right: 8px;
  bottom: 8px;
  display: flex;
  gap: 4px;
}
.card-tools button {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  padding: 0;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
  background: var(--ar-surface);
  color: var(--ar-text);
  cursor: pointer;
}
.card-tools button:hover:not(:disabled),
.card-tools button:focus-visible {
  border-color: var(--ar-primary);
  color: var(--ar-primary);
}
.card-tools button:disabled {
  opacity: 0.35;
  cursor: default;
}
.card-edit.off .card-tools button[aria-pressed='false'] {
  color: var(--ar-text-subtle);
}
</style>
