<script setup lang="ts">
import { NMenu, type MenuOption } from 'naive-ui'
import { computed, h } from 'vue'
import { useI18n } from 'vue-i18n'
import { RouterLink, useRoute } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

import { activeKey, NAVIGATION } from './navigation'

defineProps<{ collapsed: boolean }>()

const { t } = useI18n()
const route = useRoute()
const auth = useAuthStore()

const options = computed<MenuOption[]>(() =>
  NAVIGATION.filter((section) => !section.it || auth.isItStaff).map((section) => {
    const children: MenuOption[] = section.items.map((item) => ({
      key: item.key,
      label: () => h(RouterLink, { to: item.to }, () => t(item.label)),
      icon: () => h(item.icon, { size: 16, strokeWidth: 1.75 }),
    }))
    return section.label
      ? { type: 'group', key: section.key, label: t(section.label), children }
      : { type: 'group', key: section.key, children }
  }),
)

const active = computed(() => activeKey(route.name?.toString(), route.params))
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
:deep(.n-menu-item-content a) {
  color: inherit;
  text-decoration: none;
}
</style>
