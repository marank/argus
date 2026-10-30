<script setup lang="ts">
import { Plus } from '@lucide/vue'
import { NButton, NModal, NSkeleton, NTag, useMessage } from 'naive-ui'
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
  newInstance,
  resolveLayout,
  widgetType,
  type WidgetDef,
} from '@/components/dashboard/widgets'
import { useLive } from '@/composables/useLive'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'
import type { Schemas } from '@/api/types'

/** `editing`: the layout editor is open; the page header switches it on. */
const editing = defineModel<boolean>('editing', { default: false })

const { t } = useI18n()
const auth = useAuthStore()
const features = useFeaturesStore()
const message = useMessage()
const data = ref<Schemas['ITOverviewOut'] | null>(null)

const load = async () => (data.value = await dashboardApi.it())
onMounted(load)
useLive(['request', 'issue', 'asset', 'license', 'consumable', 'order'], load)

const defs = new Map(WIDGETS.map((def) => [def.id, def]))
const def = (widget: Schemas['DashboardWidgetOut']) => defs.get(widgetType(widget)) as WidgetDef
/** The name the user gave this instance, if any. */
const customTitle = (widget: Schemas['DashboardWidgetOut']) =>
  typeof widget.options.title === 'string' && widget.options.title.trim()
    ? widget.options.title.trim()
    : undefined

/** The saved layout; while editing a copy of it is changed and stored on "Done". */
const saved = computed(() => resolveLayout(WIDGETS, auth.user?.dashboard_settings.widgets))
const draft = ref<Schemas['DashboardWidgetOut'][] | null>(null)
watch(
  editing,
  (on) =>
    (draft.value = on
      ? (JSON.parse(JSON.stringify(saved.value)) as Schemas['DashboardWidgetOut'][])
      : null),
  { immediate: true },
)
const layout = computed(() => draft.value ?? saved.value)

/** Widgets of a switched-off module, and panels whose modules are all off, do not exist for this site. */
const isAvailable = (d: WidgetDef) =>
  (!d.flag || features.isOn(d.flag)) &&
  (!d.permission || auth.can(d.permission)) &&
  (!d.cards || availableCards(d, features.isOn, auth.can).length > 0)
const available = (widget: Schemas['DashboardWidgetOut']) => isAvailable(def(widget))
/** A panel with every card hidden is left out like a hidden widget. */
const hasContent = (widget: Schemas['DashboardWidgetOut']) =>
  !def(widget).cards ||
  availableCards(def(widget), features.isOn, auth.can).some(
    (c) => !widget.hidden_cards.includes(c.key),
  )

const widgets = computed(() =>
  layout.value.filter((w) => available(w) && w.visible && (editing.value || hasContent(w))),
)
/**
 * The widget list: widgets not on the dashboard, and those allowing several
 * once more (`another`) while they are on it.
 */
interface PickerEntry {
  def: WidgetDef
  /** The hidden instance to show again; none adds another one. */
  widget: Schemas['DashboardWidgetOut'] | null
  another: boolean
  /** How often it is on the dashboard already. */
  count: number
}
const addable = computed(() =>
  WIDGETS.filter(isAvailable).flatMap((d): PickerEntry[] => {
    const instances = layout.value.filter((w) => widgetType(w) === d.id)
    const count = instances.filter((w) => w.visible).length
    const hidden = instances.find((w) => !w.visible)
    if (hidden) return [{ def: d, widget: hidden, another: false, count }]
    return d.multiple ? [{ def: d, widget: null, another: true, count }] : []
  }),
)
const picking = ref(false)

/** An added widget goes to the end, where the user sees it appear. */
function add(d: WidgetDef, widget: Schemas['DashboardWidgetOut'] | null) {
  const list = draft.value
  if (!list) return
  if (widget) {
    widget.visible = true
    list.splice(list.indexOf(widget), 1)
    list.push(widget)
  } else {
    list.push(newInstance(d))
  }
  if (!addable.value.length) picking.value = false
}

/** Further instances go away entirely; the first one waits in the widget list. */
function remove(widget: Schemas['DashboardWidgetOut']) {
  if (widget.widget && draft.value) draft.value.splice(draft.value.indexOf(widget), 1)
  else widget.visible = false
}

function rename(widget: Schemas['DashboardWidgetOut'], title: string) {
  const options = { ...widget.options }
  // Stored as typed (trimmed only for display), so spaces between words survive typing.
  if (title.trim()) options.title = title
  else delete options.title
  widget.options = options
}

/**
 * A widget changes its own settings (the notes text): while editing that goes
 * into the draft, otherwise it is saved right away.
 */
async function setOptions(widget: Schemas['DashboardWidgetOut'], options: Record<string, unknown>) {
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

function move(widget: Schemas['DashboardWidgetOut'], delta: number) {
  const index = widgets.value.findIndex((w) => w.id === widget.id)
  const neighbour = widgets.value[index + delta]
  if (neighbour) moveTo(widget.id, neighbour.id)
}

function toggleCard(widget: Schemas['DashboardWidgetOut'], key: string) {
  widget.hidden_cards = widget.hidden_cards.includes(key)
    ? widget.hidden_cards.filter((k) => k !== key)
    : [...widget.hidden_cards, key]
}

function reorderCards(widget: Schemas['DashboardWidgetOut'], order: string[]) {
  const defaults = def(widget).cards?.map((c) => c.key) ?? []
  // The default order is stored as none, so a later change of the default still applies.
  widget.card_order = order.join() === defaults.join() ? [] : order
}

/* Drag and drop: the dragged widget takes the place of the one it is dragged over. */
const dragged = ref<string | null>(null)
let lastOver: string | null = null

function onDragStart(event: DragEvent, widget: Schemas['DashboardWidgetOut']) {
  dragged.value = widget.id
  lastOver = widget.id
  event.dataTransfer?.setData('text/plain', widget.id)
  if (event.dataTransfer) event.dataTransfer.effectAllowed = 'move'
}

function onDragOver(event: DragEvent, widget: Schemas['DashboardWidgetOut']) {
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
    await auth.changeDashboard({
      widgets: isDefaultLayout(WIDGETS, draft.value) ? [] : draft.value,
    })
    editing.value = false
    message.success(t('common.saved'))
  } catch {
    message.error(t('common.error'))
  } finally {
    saving.value = false
  }
}

const reset = () => (draft.value = defaultLayout(WIDGETS))

/** The editor's buttons sit in the page header (DashboardView). */
defineExpose({
  save,
  reset,
  saving,
  canAdd: computed(() => addable.value.length > 0),
  openPicker: () => (picking.value = true),
})
</script>

<template>
  <div v-if="!data" class="stack">
    <NSkeleton height="90px" :repeat="2" />
  </div>
  <div v-else class="stack">
    <p v-if="!editing && !widgets.length" class="empty muted">{{ t('dashboard.edit.empty') }}</p>
    <TransitionGroup tag="div" name="widget" class="widget-grid">
      <DashboardWidget
        v-for="(widget, index) in widgets"
        :key="widget.id"
        :title="customTitle(widget) ?? t(def(widget).title)"
        :custom-title="def(widget).multiple ? String(widget.options.title ?? '') : undefined"
        :icon="def(widget).icon"
        :settings="widget"
        :editing="editing"
        :interactive="!!def(widget).cards"
        :first="index === 0"
        :last="index === widgets.length - 1"
        :class="{ dragged: dragged === widget.id }"
        @remove="remove(widget)"
        @rename="rename(widget, $event)"
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
          :title="customTitle(widget)"
          @update:options="setOptions(widget, $event)"
        />
      </DashboardWidget>
    </TransitionGroup>
    <NModal
      v-model:show="picking"
      preset="card"
      :title="t('dashboard.edit.add')"
      class="widget-picker"
      style="width: min(880px, calc(100vw - 32px))"
      :auto-focus="false"
    >
      <ul class="picker-list">
        <li v-for="entry in addable" :key="entry.def.id">
          <component :is="entry.def.icon" :size="18" class="picker-icon" />
          <div class="picker-text">
            <div class="picker-title">
              <strong>{{ t(entry.def.title) }}</strong>
              <NTag
                v-if="entry.def.multiple"
                size="tiny"
                :bordered="false"
                type="info"
                :title="t('dashboard.edit.multipleHint')"
              >
                {{ t('dashboard.edit.multiple') }}
              </NTag>
              <small v-if="entry.count" class="mono muted">
                {{ t('dashboard.edit.onDashboard', { count: entry.count }, entry.count) }}
              </small>
            </div>
            <span class="muted">{{ t(entry.def.description) }}</span>
          </div>
          <NButton size="small" @click="add(entry.def, entry.widget)">
            <template #icon><Plus /></template>
            {{ entry.another ? t('dashboard.edit.addAnother') : t('dashboard.edit.addOne') }}
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
.empty {
  margin: 0;
}
/* Two columns of tiles; one on phones. */
.picker-list {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
  padding: 0;
  list-style: none;
}
.picker-list li {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: 12px;
  padding: 10px 12px;
  border: 1px solid var(--ar-border);
  border-radius: 3px;
}
@media (max-width: 640px) {
  .picker-list {
    grid-template-columns: minmax(0, 1fr);
  }
}
.picker-icon {
  color: var(--ar-primary);
}
.picker-text {
  display: grid;
  gap: 2px;
}
.picker-text > span {
  font-size: 12px;
}
.picker-title {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px 8px;
}
</style>
