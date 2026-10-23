<script setup lang="ts">
import { useI18n } from 'vue-i18n'
import { RouterLink, RouterView, useRoute } from 'vue-router'

import PageHeader from '@/components/common/PageHeader.vue'
import { SETTINGS_SECTIONS } from '@/components/settings/sections'

const { t } = useI18n()
const route = useRoute()
</script>

<template>
  <div class="page">
    <PageHeader :title="t('settings.title')" :subtitle="t('settings.subtitle')" />
    <div class="settings">
      <nav class="subnav" :aria-label="t('settings.title')">
        <RouterLink
          v-for="section in SETTINGS_SECTIONS"
          :key="section.name"
          :to="{ name: section.name }"
          class="entry"
          active-class="active"
          :class="{ active: route.meta.section === section.name }"
        >
          <component :is="section.icon" :size="16" :stroke-width="1.75" class="icon" />
          <span>
            <span class="label">{{ t(section.label) }}</span>
            <small class="muted">{{ t(section.description) }}</small>
          </span>
        </RouterLink>
      </nav>
      <div class="content">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<style scoped>
.settings {
  display: grid;
  grid-template-columns: 220px minmax(0, 1fr);
  gap: 28px;
  align-items: start;
}
.subnav {
  position: sticky;
  top: 16px;
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.entry {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 9px 10px;
  border-left: 2px solid transparent;
  border-radius: 0 3px 3px 0;
  color: var(--ar-text);
  text-decoration: none;
}
.entry:hover {
  background: var(--ar-surface-sunken);
  text-decoration: none;
}
.entry.active {
  background: var(--ar-primary-soft);
  border-left-color: var(--ar-primary);
}
.entry.active .icon {
  color: var(--ar-primary);
}
.icon {
  flex: none;
  margin-top: 2px;
  color: var(--ar-text-muted);
}
.label {
  display: block;
  font-size: 13px;
  font-weight: 500;
}
small {
  display: block;
  margin-top: 2px;
  font-size: 11.5px;
  line-height: 1.4;
}
.content {
  min-width: 0;
  /* Groups and rows adapt to the space next to the sub-navigation, not the window. */
  container-type: inline-size;
}
@media (max-width: 960px) {
  .settings {
    grid-template-columns: minmax(0, 1fr);
    gap: 16px;
  }
  .subnav {
    position: static;
    flex-direction: row;
    overflow-x: auto;
    border-bottom: 1px solid var(--ar-border);
  }
  .entry {
    border-left: none;
    border-bottom: 2px solid transparent;
    border-radius: 0;
  }
  .entry.active {
    border-bottom-color: var(--ar-primary);
  }
  small {
    display: none;
  }
}
</style>
