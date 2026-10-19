import { usePreferredDark, useStorage } from '@vueuse/core'
import { darkTheme } from 'naive-ui'
import { computed, watchEffect } from 'vue'

import { darkOverrides, lightOverrides } from './overrides'
import { darkPalette, lightPalette, type Palette } from './palette'

export type ThemeMode = 'light' | 'dark' | 'system'

const mode = useStorage<ThemeMode>('argus.theme', 'system')
const prefersDark = usePreferredDark()
const isDark = computed(
  () => mode.value === 'dark' || (mode.value === 'system' && prefersDark.value),
)

function toCssVariables(palette: Palette) {
  const root = document.documentElement
  for (const [key, value] of Object.entries(palette)) {
    root.style.setProperty(`--ar-${key.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`)}`, value)
  }
}

watchEffect(() => {
  document.documentElement.dataset.theme = isDark.value ? 'dark' : 'light'
  toCssVariables(isDark.value ? darkPalette : lightPalette)
})

export function useTheme() {
  return {
    mode,
    isDark,
    naiveTheme: computed(() => (isDark.value ? darkTheme : null)),
    overrides: computed(() => (isDark.value ? darkOverrides : lightOverrides)),
    toggle: () => (mode.value = isDark.value ? 'light' : 'dark'),
  }
}
