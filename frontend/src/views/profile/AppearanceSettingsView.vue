<script setup lang="ts">
import { Check } from '@lucide/vue'
import { useMessage } from 'naive-ui'
import { useI18n } from 'vue-i18n'

import PageHeader from '@/components/common/PageHeader.vue'
import SettingsGroup from '@/components/settings/SettingsGroup.vue'
import { useAuthStore } from '@/stores/auth'
import { THEME_ICONS } from '@/theme/icons'
import type { Palette } from '@/theme/palette'
import { THEME_GROUPS, THEMES, useTheme, type ThemeMode } from '@/theme/useTheme'

/**
 * The user's colour theme, saved in the profile, grouped into the system setting, light and
 * dark themes. Each choice shows a small preview drawn from its palette; "system" shows the
 * light and the dark theme side by side.
 */
const { t } = useI18n()
const message = useMessage()
const auth = useAuthStore()
const { mode } = useTheme()

const previews = (value: ThemeMode): Palette[] =>
  value === 'system' ? [THEMES.light.palette, THEMES.dark.palette] : [THEMES[value].palette]

async function choose(theme: ThemeMode) {
  if (theme === mode.value) return
  try {
    await auth.changeTheme(theme)
    message.success(t('common.saved'))
  } catch {
    message.error(t('common.error'))
  }
}
</script>

<template>
  <div class="page narrow">
    <PageHeader
      :title="t('profile.appearance.title')"
      :subtitle="t('profile.appearance.subtitle')"
    />
    <SettingsGroup
      :title="t('profile.appearance.theme')"
      :description="t('profile.appearance.themeDescription')"
    >
      <div
        v-for="group in THEME_GROUPS"
        :key="group.key"
        class="group"
        role="radiogroup"
        :aria-label="t(`profile.appearance.groups.${group.key}`)"
      >
        <h3 class="eyebrow">{{ t(`profile.appearance.groups.${group.key}`) }}</h3>
        <div class="themes">
          <button
            v-for="value in group.modes"
            :key="value"
            type="button"
            role="radio"
            class="theme"
            :class="{ active: mode === value }"
            :aria-checked="mode === value"
            :data-theme-option="value"
            @click="choose(value)"
          >
            <span class="preview">
              <span
                v-for="(p, i) in previews(value)"
                :key="i"
                class="half"
                :style="{ background: p.bg, color: p.text }"
              >
                <span class="side" :style="{ background: p.surface, borderColor: p.border }" />
                <span class="card" :style="{ background: p.surface, borderColor: p.border }">
                  <span class="line" :style="{ background: p.text }" />
                  <span class="line short" :style="{ background: p.textSubtle }" />
                  <span class="button" :style="{ background: p.primary }" />
                </span>
              </span>
            </span>
            <span class="label">
              <component :is="THEME_ICONS[value]" :size="14" />
              {{ t(`nav.themes.${value}`) }}
              <Check v-if="mode === value" :size="14" class="check" />
            </span>
          </button>
        </div>
      </div>
    </SettingsGroup>
  </div>
</template>

<style scoped>
.narrow {
  max-width: 900px;
}
.group + .group {
  margin-top: 18px;
}
.group h3 {
  margin: 0 0 8px;
}
.themes {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}
.theme {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 6px 6px 8px;
  border: 1px solid var(--ar-border);
  border-radius: 4px;
  background: var(--ar-surface);
  color: var(--ar-text);
  font: inherit;
  text-align: left;
  cursor: pointer;
  transition: border-color 0.12s ease;
}
.theme:hover {
  border-color: var(--ar-border-strong);
}
.theme:focus-visible {
  outline: 2px solid var(--ar-primary);
  outline-offset: 1px;
}
.theme.active {
  border-color: var(--ar-primary);
  box-shadow: 0 0 0 1px var(--ar-primary);
}
.preview {
  display: flex;
  height: 72px;
  overflow: hidden;
  border-radius: 3px;
  border: 1px solid var(--ar-border);
}
.half {
  position: relative;
  flex: 1;
}
.side {
  position: absolute;
  inset: 0 auto 0 0;
  width: 14px;
  border-right: 1px solid;
}
.card {
  position: absolute;
  top: 10px;
  left: 22px;
  right: 8px;
  display: flex;
  flex-direction: column;
  gap: 5px;
  padding: 7px;
  border: 1px solid;
  border-radius: 2px;
}
.line {
  height: 4px;
  width: 70%;
  border-radius: 2px;
}
.line.short {
  width: 45%;
}
.button {
  width: 32px;
  height: 9px;
  margin-top: 2px;
  border-radius: 2px;
}
.label {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 0 2px;
  font-weight: 500;
}
.check {
  margin-left: auto;
  color: var(--ar-primary);
}
</style>
