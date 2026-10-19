import {
  Barcode,
  Box,
  Cable,
  Cpu,
  Headphones,
  Keyboard,
  Laptop,
  Monitor,
  Package,
  Plug,
  Printer,
  Smartphone,
  Tablet,
} from '@lucide/vue'
import type { Component } from 'vue'

/** Icons selectable for device groups (stored by name in the backend). */
export const CATEGORY_ICONS: Record<string, Component> = {
  laptop: Laptop,
  desktop: Monitor,
  mobile: Smartphone,
  tablet: Tablet,
  headphones: Headphones,
  keyboard: Keyboard,
  barcode: Barcode,
  plug: Plug,
  cable: Cable,
  printer: Printer,
  cpu: Cpu,
  box: Box,
}

export function categoryIcon(name: string | null | undefined): Component {
  return (name && CATEGORY_ICONS[name]) || Package
}
