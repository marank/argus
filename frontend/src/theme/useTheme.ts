import { usePreferredDark, useStorage } from '@vueuse/core'
import { darkTheme, type GlobalThemeOverrides } from 'naive-ui'
import { computed, watchEffect } from 'vue'

import type { Schemas } from '@/api/types'
import { allValues } from '@/utils/enums'

import { darkOverrides, lightOverrides, retroOverrides, solarizedOverrides } from './overrides'
import { darkPalette, lightPalette, retroPalette, solarizedPalette, type Palette } from './palette'

/** The user's choice; "system" follows the device's light or dark setting. */
export type ThemeMode = Schemas['Theme']
/** The theme actually shown. */
export type Theme = Exclude<ThemeMode, 'system'>

export const THEME_MODES = allValues<ThemeMode>({
  system: true,
  light: true,
  solarized: true,
  dark: true,
  retro: true,
})

export const THEMES: Record<
  Theme,
  { palette: Palette; overrides: GlobalThemeOverrides; dark: boolean }
> = {
  light: { palette: lightPalette, overrides: lightOverrides, dark: false },
  solarized: { palette: solarizedPalette, overrides: solarizedOverrides, dark: false },
  dark: { palette: darkPalette, overrides: darkOverrides, dark: true },
  retro: { palette: retroPalette, overrides: retroOverrides, dark: true },
}

/** The choices as offered: the system setting on its own, then the light and the dark themes. */
export const THEME_GROUPS: { key: 'system' | 'light' | 'dark'; modes: ThemeMode[] }[] = [
  { key: 'system', modes: ['system'] },
  ...(['light', 'dark'] as const).map((key) => ({
    key,
    modes: THEME_MODES.filter(
      (mode) => mode !== 'system' && THEMES[mode].dark === (key === 'dark'),
    ),
  })),
]

// Kept in the browser as well, so the login page and the first paint already show the
// user's theme; the profile setting (see the auth store) takes over once signed in.
const mode = useStorage<ThemeMode>('argus.theme', 'system')
const prefersDark = usePreferredDark()
const theme = computed<Theme>(() => {
  if (mode.value in THEMES) return mode.value as Theme
  return prefersDark.value ? 'dark' : 'light'
})
const isDark = computed(() => THEMES[theme.value].dark)

function toCssVariables(palette: Palette) {
  const root = document.documentElement
  for (const [key, value] of Object.entries(palette)) {
    root.style.setProperty(`--ar-${key.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`)}`, value)
  }
}

watchEffect(() => {
  document.documentElement.dataset.theme = theme.value
  toCssVariables(THEMES[theme.value].palette)
})

export function useTheme() {
  return {
    mode,
    theme,
    isDark,
    naiveTheme: computed(() => (isDark.value ? darkTheme : null)),
    overrides: computed(() => THEMES[theme.value].overrides),
  }
}
