import { CassetteTape, Monitor, Moon, Sun, Sunset } from '@lucide/vue'
import type { Component } from 'vue'

import type { ThemeMode } from './useTheme'

export const THEME_ICONS: Record<ThemeMode, Component> = {
  system: Monitor,
  light: Sun,
  dark: Moon,
  solarized: Sunset,
  retro: CassetteTape,
}
