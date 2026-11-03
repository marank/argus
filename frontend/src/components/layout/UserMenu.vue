<script setup lang="ts">
import { Bell, ChevronDown, Languages, LogOut, Palette, Settings, ShieldCheck } from '@lucide/vue'
import { NButton, NDropdown, type DropdownOption } from 'naive-ui'
import { computed, h, type Component } from 'vue'
import { useI18n } from 'vue-i18n'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { THEME_ICONS } from '@/theme/icons'
import { THEME_GROUPS, useTheme, type ThemeMode } from '@/theme/useTheme'

const { t, locale } = useI18n()
const auth = useAuthStore()
const router = useRouter()
const { mode } = useTheme()

const icon = (component: Component) => () => h(component, { size: 15 })
const check = (active: boolean) => (active ? ' ✓' : '')

const options = computed<DropdownOption[]>(() => [
  {
    type: 'group',
    key: 'theme',
    label: t('nav.theme'),
    // System, light and dark themes, each set apart by a line as on the appearance page.
    children: THEME_GROUPS.flatMap(({ key, modes }, index) => [
      ...(index ? [{ type: 'divider', key: `theme-${key}` }] : []),
      ...modes.map((value) => ({
        key: `theme:${value}`,
        label: t(`nav.themes.${value}`) + check(mode.value === value),
        icon: icon(THEME_ICONS[value]),
      })),
    ]),
  },
  { type: 'divider', key: 'd1' },
  {
    type: 'group',
    key: 'language',
    label: t('nav.language'),
    children: [
      { key: 'lang:de', label: 'Deutsch' + check(locale.value === 'de'), icon: icon(Languages) },
      { key: 'lang:en', label: 'English' + check(locale.value === 'en'), icon: icon(Languages) },
    ],
  },
  { type: 'divider', key: 'd2' },
  { key: 'appearance', label: t('profile.appearance.title'), icon: icon(Palette) },
  { key: 'notifications', label: t('profile.notifications.title'), icon: icon(Bell) },
  { key: 'security', label: t('profile.security.title'), icon: icon(ShieldCheck) },
  ...(auth.isItStaff ? [{ key: 'admin', label: t('nav.admin'), icon: icon(Settings) }] : []),
  { key: 'logout', label: t('nav.logout'), icon: icon(LogOut) },
])

async function onSelect(key: string) {
  const [kind, value] = key.split(':')
  if (kind === 'theme') await auth.changeTheme(value as ThemeMode)
  else if (kind === 'lang') await auth.changeLanguage(value as 'en' | 'de')
  else if (kind === 'admin') window.open('/admin/', '_blank')
  else if (kind === 'appearance') router.push({ name: 'profile-appearance' })
  else if (kind === 'notifications') router.push({ name: 'profile-notifications' })
  else if (kind === 'security') router.push({ name: 'profile-security' })
  else if (kind === 'logout') {
    await auth.logout()
    router.push({ name: 'login' })
  }
}

const initials = computed(() =>
  (auth.user?.display_name ?? '?')
    .split(' ')
    .map((part) => part[0])
    .join('')
    .slice(0, 2)
    .toUpperCase(),
)
</script>

<template>
  <NDropdown :options="options" trigger="click" placement="bottom-end" @select="onSelect">
    <NButton quaternary size="small" class="user">
      <span class="avatar mono">{{ initials }}</span>
      <span class="name">
        {{ auth.user?.display_name }}
        <small v-if="auth.isItStaff" class="eyebrow">IT</small>
      </span>
      <ChevronDown :size="14" />
    </NButton>
  </NDropdown>
</template>

<style scoped>
.user {
  height: 34px;
  padding: 0 6px;
}
.user :deep(.n-button__content) {
  gap: 8px;
}
.avatar {
  display: grid;
  place-items: center;
  width: 24px;
  height: 24px;
  border-radius: 3px;
  background: var(--ar-primary-soft);
  color: var(--ar-primary);
  font-size: 11px;
  font-weight: 700;
}
.name {
  display: flex;
  align-items: baseline;
  gap: 6px;
}
@media (max-width: 720px) {
  .name {
    display: none;
  }
}
</style>
