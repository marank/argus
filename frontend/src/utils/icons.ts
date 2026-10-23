import {
  AppWindow,
  Barcode,
  Box,
  Briefcase,
  Building2,
  Cable,
  Calculator,
  Cloud,
  Cpu,
  Headphones,
  Headset,
  Keyboard,
  KeyRound,
  Laptop,
  Megaphone,
  Monitor,
  Package,
  Plug,
  Printer,
  ShieldCheck,
  ShoppingCart,
  Smartphone,
  Store,
  Tablet,
  Truck,
  Users,
  Warehouse,
  Wrench,
} from '@lucide/vue'
import type { Component } from 'vue'

/** Icons selectable for categories (stored by name in the backend). */
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
  app: AppWindow,
  key: KeyRound,
  cloud: Cloud,
  shield: ShieldCheck,
}

export function categoryIcon(name: string | null | undefined): Component {
  return (name && CATEGORY_ICONS[name]) || Package
}

/** Icons selectable for departments (the backend's `Department.Icon`). */
export const DEPARTMENT_ICONS: Record<string, Component> = {
  building: Building2,
  briefcase: Briefcase,
  users: Users,
  monitor: Monitor,
  cart: ShoppingCart,
  store: Store,
  headset: Headset,
  megaphone: Megaphone,
  calculator: Calculator,
  truck: Truck,
  warehouse: Warehouse,
  wrench: Wrench,
}

export function departmentIcon(name: string | null | undefined): Component {
  return (name && DEPARTMENT_ICONS[name]) || Building2
}
