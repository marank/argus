<script setup lang="ts">
import { ChevronDown } from '@lucide/vue'
import { NMenu, type MenuOption } from 'naive-ui'
import { useStorage } from '@vueuse/core'
import { computed, h, watch } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'

import { activeKey, NAVIGATION } from './navigation'

const props = defineProps<{ collapsed: boolean }>()

const { t } = useI18n()
const route = useRoute()
const auth = useAuthStore()
const features = useFeaturesStore()

const active = computed(() => activeKey(route.name?.toString(), route.params))

/** Folded sections, remembered per browser; the section of the current page always opens. */
const folded = useStorage<string[]>('argus.sidebar-folded', [])
const isFolded = (key: string) => folded.value.includes(key)
function toggle(key: string) {
  folded.value = isFolded(key) ? folded.value.filter((k) => k !== key) : [...folded.value, key]
}
watch(
  active,
  (key) => {
    const section = NAVIGATION.find((s) => s.label && s.items.some((i) => i.key === key))
    if (section && isFolded(section.key)) toggle(section.key)
  },
  { immediate: true },
)

/**
 * A section heading; where sections fold, a button with an arrow that folds the
 * entries away. Always the same wrapper: the menu must not swap a plain text
 * label for an element when the sidebar collapses, or its update fails.
 */
function sectionTitle(key: string, label: string, canFold: boolean) {
  const open = !isFolded(key)
  return () =>
    h(
      'span',
      { class: 'section-title' },
      canFold
        ? h(
            'button',
            {
              type: 'button',
              class: 'section-toggle',
              'aria-expanded': open,
              onClick: () => toggle(key),
            },
            [h('span', label), h(ChevronDown, { size: 13, class: ['chevron', { open }] })],
          )
        : label,
    )
}

const sections = computed(() =>
  NAVIGATION.filter(
    (section) => (!section.it || auth.isItStaff) && (!section.superuser || auth.isSuperuser),
  )
    .map((section) => ({
      ...section,
      items: section.items.filter((item) => !item.module || features.isOn(item.module)),
    }))
    // Sections whose modules are all switched off disappear.
    .filter((section) => section.items.length),
)

/**
 * Sections fold only when there is something to choose between (employees see a
 * single one) and the sidebar is wide enough to show headings.
 */
const foldable = computed(
  () => !props.collapsed && sections.value.filter((section) => section.label).length > 1,
)

const options = computed<MenuOption[]>(() =>
  sections.value.flatMap<MenuOption>((section) => {
    const children: MenuOption[] = section.items.map((item) => ({
      key: item.key,
      label: () => h(RouterLink, { to: item.to }, () => t(item.label)),
      icon: () => h(item.icon, { size: 16, strokeWidth: 1.75 }),
    }))
    // Without a heading the entries stand alone; an empty group would still leave a gap.
    if (!section.label) return children
    return {
      type: 'group',
      key: section.key,
      label: sectionTitle(section.key, t(section.label), foldable.value),
      children,
    }
  }),
)

/**
 * Entries of a folded section stay in the menu and slide shut (see the styles),
 * so folding and unfolding is animated.
 */
const sectionOf = computed(
  () => new Map(sections.value.flatMap((s) => s.items.map((i) => [i.key, s.key] as const))),
)
const nodeProps = (option: MenuOption) => {
  const section = sectionOf.value.get(String(option.key))
  return foldable.value && section && isFolded(section) ? { class: 'folded' } : {}
}
</script>

<template>
  <nav class="sidebar" :class="{ collapsed }">
    <RouterLink to="/" class="brand">
      <svg viewBox="0 0 32 32" width="22" height="22" aria-hidden="true">
        <circle cx="16" cy="16" r="10" fill="none" stroke="currentColor" stroke-width="2.4" />
        <circle cx="16" cy="16" r="3.6" fill="currentColor" />
        <path
          d="M16 2v5M16 25v5M2 16h5M25 16h5"
          stroke="currentColor"
          stroke-width="2.4"
          stroke-linecap="round"
        />
      </svg>
      <span v-if="!collapsed" class="wordmark">ARGUS</span>
    </RouterLink>
    <NMenu
      :value="active"
      :options="options"
      :collapsed="collapsed"
      :collapsed-width="56"
      :collapsed-icon-size="18"
      :indent="16"
      :node-props="nodeProps"
    />
  </nav>
</template>

<style scoped>
.sidebar {
  display: flex;
  flex-direction: column;
  height: 100%;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  height: var(--ar-header-height);
  padding: 0 17px;
  border-bottom: 1px solid var(--ar-border);
  color: var(--ar-primary);
  text-decoration: none;
  flex-shrink: 0;
}
.wordmark {
  font-family: var(--ar-font-mono);
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 0.28em;
  color: var(--ar-text);
}
:deep(.n-menu-item-group-title) {
  font-family: var(--ar-font-mono);
  font-size: 10.5px;
  letter-spacing: 0.08em;
  text-transform: uppercase;
  color: var(--ar-text-subtle) !important;
  padding-top: 14px !important;
}
/* Collapsed: group titles become thin separators. */
.collapsed :deep(.n-menu-item-group-title) {
  height: 1px;
  padding: 0 !important;
  margin: 8px 12px;
  overflow: hidden;
  background: var(--ar-border);
  color: transparent !important;
}
/*
 * Folding: entries slide shut and fade; once shut they are hidden, so the
 * keyboard skips them. Unfolding reverses it, visible from the start.
 */
.sidebar :deep(.n-menu-item) {
  overflow: hidden;
  transition:
    height 0.2s ease,
    margin-top 0.2s ease,
    opacity 0.15s ease,
    visibility 0s linear 0s;
}
.sidebar :deep(.n-menu-item.folded) {
  height: 0;
  margin-top: 0;
  opacity: 0;
  visibility: hidden;
  transition:
    height 0.2s ease,
    margin-top 0.2s ease,
    opacity 0.15s ease,
    visibility 0s linear 0.2s;
}
@media (prefers-reduced-motion: reduce) {
  .sidebar :deep(.n-menu-item),
  .sidebar :deep(.n-menu-item.folded) {
    transition: none;
  }
}
/* Fills the (flex) group title, so the toggle inside spans the width and its arrow sits on the right. */
:deep(.section-title) {
  display: block;
  flex: 1;
  min-width: 0;
}
:deep(.section-toggle) {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  /* The arrow ends where the entries' content ends. */
  padding: 0 18px 0 0;
  border: none;
  background: none;
  color: inherit;
  font: inherit;
  letter-spacing: inherit;
  text-transform: inherit;
  cursor: pointer;
}
:deep(.section-toggle:hover) {
  color: var(--ar-text-muted);
}
:deep(.section-toggle .chevron) {
  transform: rotate(-90deg);
  transition: transform 0.15s ease;
}
:deep(.section-toggle .chevron.open) {
  transform: none;
}
:deep(.n-menu-item-content a) {
  color: inherit;
  text-decoration: none;
}
</style>
