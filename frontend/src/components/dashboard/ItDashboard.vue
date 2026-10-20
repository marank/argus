<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { NButton, NModal, NSkeleton, useMessage } from 'naive-ui'
import { computed, onMounted, ref, watch } from 'vue'
import { useI18n } from 'vue-i18n'

import { dashboardApi } from '@/api/dashboard'
import DashboardWidget from '@/components/dashboard/DashboardWidget.vue'
import StatGroupWidget from '@/components/dashboard/widgets/StatGroupWidget.vue'
import {
  WIDGETS,
  availableCards,
  defaultLayout,
  isDefaultLayout,
  resolveLayout,
  type WidgetDef,
} from '@/components/dashboard/widgets'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'
import type { WidgetSettings } from '@/types/accounts'
import type { ITOverview } from '@/types/dashboard'

/** `editing`: the layout editor is open; the page header switches it on. */
const editing = defineModel<boolean>('editing', { default: false })

const { t } = useI18n()
const auth = useAuthStore()
const features = useFeaturesStore()
const message = useMessage()
const data = ref<ITOverview | null>(null)

onMounted(async () => (data.value = await dashboardApi.it()))

const defs = new Map(WIDGETS.map((def) => [def.id, def]))
const def = (widget: WidgetSettings) => defs.get(widget.id) as WidgetDef

/** The saved layout; while editing a copy of it is changed and stored on "Done". */
const saved = computed(() => resolveLayout(WIDGETS, auth.user?.dashboard_settings?.widgets))
const draft = ref<WidgetSettings[] | null>(null)
watch(
  editing,
  (on) => (draft.value = on ? (JSON.parse(JSON.stringify(saved.value)) as WidgetSettings[]) : null),
  { immediate: true },
)
const layout = computed(() => draft.value ?? saved.value)

/** Widgets of a switched-off module, and panels whose modules are all off, do not exist for this site. */
const available = (widget: WidgetSettings) =>
  (!def(widget).flag || features.isOn(def(widget).flag!)) &&
  (!def(widget).cards || availableCards(def(widget), features.isOn).length > 0)
/** A panel with every card hidden is left out like a hidden widget. */
const hasContent = (widget: WidgetSettings) =>
  !def(widget).cards ||
  availableCards(def(widget), features.isOn).some((c) => !widget.hidden_cards.includes(c.key))

const widgets = computed(() =>
  layout.value.filter((w) => available(w) && w.visible && (editing.value || hasContent(w))),
)
/** Widgets that are not on the dashboard, offered in the widget list. */
const addable = computed(() => layout.value.filter((w) => available(w) && !w.visible))
const picking = ref(false)

/** An added widget goes to the end, where the user sees it appear. */
function add(widget: WidgetSettings) {
  const list = draft.value
  if (!list) return
  widget.visible = true
  list.splice(list.indexOf(widget), 1)
  list.push(widget)
  if (!addable.value.length) picking.value = false
}

/**
 * A widget changes its own settings (the notes text): while editing that goes
 * into the draft, otherwise it is saved right away.
 */
async function setOptions(widget: WidgetSettings, options: Record<string, unknown>) {
  if (draft.value) {
    widget.options = options
    return
  }
  const layout = saved.value.map((w) => (w.id === widget.id ? { ...w, options } : w))
  try {
    await auth.changeDashboard({ widgets: layout })
  } catch {
    message.error(t('common.error'))
  }
}

function moveTo(id: string, targetId: string) {
  const list = draft.value
  if (!list) return
  const from = list.findIndex((w) => w.id === id)
  const to = list.findIndex((w) => w.id === targetId)
  if (from < 0 || to < 0 || from === to) return
  const [widget] = list.splice(from, 1)
  list.splice(to, 0, widget!)
}

function move(widget: WidgetSettings, delta: number) {
  const index = widgets.value.findIndex((w) => w.id === widget.id)
  const neighbour = widgets.value[index + delta]
  if (neighbour) moveTo(widget.id, neighbour.id)
}

function toggleCard(widget: WidgetSettings, key: string) {
  widget.hidden_cards = widget.hidden_cards.includes(key)
    ? widget.hidden_cards.filter((k) => k !== key)
    : [...widget.hidden_cards, key]
}

function reorderCards(widget: WidgetSettings, order: string[]) {
  const defaults = def(widget).cards?.map((c) => c.key) ?? []
  // The default order is stored as none, so a later change of the default still applies.
  widget.card_order = order.join() === defaults.join() ? [] : order
}

/* Drag and drop: the dragged widget takes the place of the one it is dragged over. */
const dragged = ref<string | null>(null)
let lastOver: string | null = null

function onDragStart(event: DragEvent, widget: WidgetSettings) {
  dragged.value = widget.id
  lastOver = widget.id
  event.dataTransfer?.setData('text/plain', widget.id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDragOver(event: DragEvent, widget: WidgetSettings) {
  if (!dragged.value) return
  event.preventDefault()
  // Only on entering another widget, so a smaller one does not flip back and forth.
  if (widget.id !== lastOver && widget.id !== dragged.value) moveTo(dragged.value, widget.id)
  lastOver = widget.id
}

function onDragEnd() {
  dragged.value = null
  lastOver = null
}

const saving = ref(false)

async function save() {
  if (!draft.value) return
  saving.value = true
  try {
    await auth.changeDashboard(
      isDefaultLayout(WIDGETS, draft.value) ? {} : { widgets: draft.value },
    )
    editing.value = false
    message.success(t('common.saved'))
  } catch {
    message.error(t('common.error'))
  } finally {
    saving.value = false
  }
}

const reset = () => (draft.value = defaultLayout(WIDGETS))
</script>

<template>
  <div v-if="!data" class="stack">
    <NSkeleton height="90px" :repeat="2" />
  </div>
  <div v-else class="stack">
    <div v-if="editing" class="editor-bar">
      <p class="muted">{{ t('dashboard.edit.hint') }}</p>
      <div class="row">
        <NButton size="small" :disabled="!addable.length" @click="picking = true">
          <template #icon><Plus /></template>
          {{ t('dashboard.edit.add') }}
        </NButton>
        <NButton size="small" quaternary @click="reset">{{ t('dashboard.edit.reset') }}</NButton>
        <NButton size="small" @click="editing = false">{{ t('common.cancel') }}</NButton>
        <NButton size="small" type="primary" :loading="saving" @click="save">
          {{ t('dashboard.edit.done') }}
        </NButton>
      </div>
    </div>
    <p v-if="!editing && !widgets.length" class="empty muted">{{ t('dashboard.edit.empty') }}</p>
    <TransitionGroup tag="div" name="widget" class="widget-grid">
      <DashboardWidget
        v-for="(widget, index) in widgets"
        :key="widget.id"
        :title="t(def(widget).title)"
        :icon="def(widget).icon"
        :settings="widget"
        :editing="editing"
        :interactive="!!def(widget).cards"
        :first="index === 0"
        :last="index === widgets.length - 1"
        :class="{ dragged: dragged === widget.id }"
        @remove="widget.visible = false"
        @resize="widget.size = $event"
        @set-height="widget.height = $event"
        @move="move(widget, $event)"
        @dragstart="onDragStart($event, widget)"
        @dragover="onDragOver($event, widget)"
        @drop.prevent
        @dragend="onDragEnd"
      >
        <StatGroupWidget
          v-if="def(widget).cards"
          :def="def(widget)"
          :data="data"
          :hidden-cards="widget.hidden_cards"
          :card-order="widget.card_order"
          :editing="editing"
          @toggle-card="toggleCard(widget, $event)"
          @reorder="reorderCards(widget, $event)"
        />
        <component
          :is="def(widget).component"
          v-else
          :data="data"
          :options="widget.options"
          @update:options="setOptions(widget, $event)"
        />
      </DashboardWidget>
    </TransitionGroup>
    <NModal
      v-model:show="picking"
      preset="card"
      :title="t('dashboard.edit.add')"
      class="widget-picker"
      style="width: min(560px, calc(100vw - 32px))"
      :auto-focus="false"
    >
      <ul class="picker-list">
        <li v-for="widget in addable" :key="widget.id">
          <component :is="def(widget).icon" :size="18" class="picker-icon" />
          <div class="picker-text">
            <strong>{{ t(def(widget).title) }}</strong>
            <span class="muted">{{ t(def(widget).description) }}</span>
          </div>
          <NButton size="small" @click="add(widget)">
            <template #icon><Plus /></template>
            {{ t('dashboard.edit.addOne') }}
          </NButton>
        </li>
      </ul>
    </NModal>
  </div>
</template>

<style scoped>
.widget-grid {
  display: grid;
  grid-template-columns: repeat(6, minmax(0, 1fr));
  gap: 12px 16px;
  align-items: stretch;
}
.widget-move {
  transition: transform 0.2s ease;
}
.dragged {
  opacity: 0.5;
}
.editor-bar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px 16px;
  padding: 10px 14px;
  border: 1px solid var(--ar-primary);
  border-radius: 3px;
  background: color-mix(in srgb, var(--ar-primary) 8%, var(--ar-surface));
}
.editor-bar p {
  margin: 0;
}
.editor-bar .row {
  flex-wrap: wrap;
}
.empty {
  margin: 0;
}
.picker-list {
  display: grid;
  margin: 0;
  padding: 0;
  list-style: none;
}
.picker-list li {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
  border-bottom: 1px solid var(--ar-border);
}
.picker-list li:last-child {
  border-bottom: none;
}
.picker-icon {
  color: var(--ar-primary);
}
.picker-text {
  display: grid;
  gap: 2px;
}
.picker-text span {
  font-size: 12px;
}
</style>
