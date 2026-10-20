import {
  AppWindow,
  Boxes,
  CalendarDays,
  ClipboardCheck,
  Building2,
  ClipboardList,
  Factory,
  FolderTree,
  Hash,
  KeyRound,
  LayoutDashboard,
  ListChecks,
  MapPin,
  MessageSquareWarning,
  MonitorSmartphone,
  PackagePlus,
  Shapes,
  ShieldCheck,
  ShoppingCart,
  SlidersHorizontal,
  Truck,
  UserRound,
  Users,
  UsersRound,
  Wrench,
} from '@lucide/vue'
import type { Component } from 'vue'
import type { RouteLocationRaw } from 'vue-router'

import type { PermissionKey } from '@/types/accounts'
import type { ModuleKey } from '@/types/settings'

export interface NavItem {
  key: string
  /** Hidden while this module is switched off in the site settings. */
  module?: ModuleKey
  /** Only for department approvers. */
  approver?: boolean
  /** Hidden unless the user's roles allow reading this area. */
  permission?: PermissionKey
  /** Only for administrators. */
  superuser?: boolean
  label: string
  icon: Component
  to: RouteLocationRaw
}

export interface NavSection {
  key: string
  label?: string
  it?: boolean
  superuser?: boolean
  items: NavItem[]
}

export const NAVIGATION: NavSection[] = [
  {
    key: 'main',
    items: [
      {
        key: 'dashboard',
        label: 'nav.dashboard',
        icon: LayoutDashboard,
        to: { name: 'dashboard' },
      },
    ],
  },
  {
    key: 'portal',
    label: 'nav.selfService',
    items: [
      { key: 'portal-new', label: 'nav.newRequest', icon: PackagePlus, to: { name: 'portal-new' } },
      {
        key: 'portal-requests',
        label: 'nav.myRequests',
        icon: ClipboardList,
        to: { name: 'portal-requests' },
      },
      {
        key: 'portal-approvals',
        approver: true,
        label: 'nav.approvals',
        icon: ClipboardCheck,
        to: { name: 'portal-approvals' },
      },
      {
        key: 'portal-devices',
        label: 'nav.myDevices',
        icon: UserRound,
        to: { name: 'portal-devices' },
      },
      {
        key: 'portal-licenses',
        module: 'licenses',
        label: 'nav.mySoftware',
        icon: AppWindow,
        to: { name: 'portal-licenses' },
      },
      {
        key: 'portal-issues',
        module: 'issues',
        label: 'nav.myIssues',
        icon: MessageSquareWarning,
        to: { name: 'portal-issues' },
      },
    ],
  },
  {
    key: 'it',
    label: 'nav.it',
    it: true,
    items: [
      {
        key: 'reservations',
        permission: 'reservations',
        label: 'nav.reservations',
        icon: ListChecks,
        to: { name: 'reservations' },
      },
      {
        key: 'calendar',
        permission: 'reservations',
        module: 'calendar',
        label: 'nav.calendar',
        icon: CalendarDays,
        to: { name: 'calendar' },
      },
      {
        key: 'assets',
        permission: 'assets',
        label: 'nav.assets',
        icon: MonitorSmartphone,
        to: { name: 'assets' },
      },
      {
        key: 'consumables',
        permission: 'consumables',
        module: 'consumables',
        label: 'nav.consumables',
        icon: Boxes,
        to: { name: 'consumables' },
      },
      {
        key: 'licenses',
        permission: 'licenses',
        module: 'licenses',
        label: 'nav.licenses',
        icon: KeyRound,
        to: { name: 'licenses' },
      },
      {
        key: 'issues',
        permission: 'issues',
        module: 'issues',
        label: 'nav.issues',
        icon: MessageSquareWarning,
        to: { name: 'issues' },
      },
      {
        key: 'event-log',
        permission: 'assets',
        label: 'nav.eventLog',
        icon: Wrench,
        to: { name: 'event-log' },
      },
    ],
  },
  {
    key: 'procurement',
    label: 'nav.procurement',
    it: true,
    items: [
      {
        key: 'needs',
        permission: 'procurement',
        module: 'procurement',
        label: 'nav.needs',
        icon: ShoppingCart,
        to: { name: 'needs' },
      },
      {
        key: 'orders',
        permission: 'procurement',
        module: 'procurement',
        label: 'nav.orders',
        icon: Truck,
        to: { name: 'orders' },
      },
    ],
  },
  {
    key: 'masterdata',
    label: 'nav.masterdata',
    it: true,
    items: [
      {
        key: 'md-models',
        permission: 'models',
        label: 'masterdata.resources.models',
        icon: Shapes,
        to: { name: 'masterdata', params: { resource: 'models' } },
      },
      {
        key: 'md-categories',
        permission: 'categories',
        label: 'masterdata.resources.categories',
        icon: FolderTree,
        to: { name: 'masterdata', params: { resource: 'categories' } },
      },
      {
        key: 'md-manufacturers',
        permission: 'manufacturers',
        label: 'masterdata.resources.manufacturers',
        icon: Factory,
        to: { name: 'masterdata', params: { resource: 'manufacturers' } },
      },
      {
        key: 'md-suppliers',
        permission: 'suppliers',
        label: 'masterdata.resources.suppliers',
        icon: Truck,
        to: { name: 'masterdata', params: { resource: 'suppliers' } },
      },
      {
        key: 'md-locations',
        permission: 'locations',
        label: 'masterdata.resources.locations',
        icon: MapPin,
        to: { name: 'masterdata', params: { resource: 'locations' } },
      },
      {
        key: 'md-departments',
        permission: 'departments',
        label: 'masterdata.resources.departments',
        icon: Building2,
        to: { name: 'masterdata', params: { resource: 'departments' } },
      },
      {
        key: 'md-teams',
        permission: 'teams',
        label: 'masterdata.resources.teams',
        icon: UsersRound,
        to: { name: 'masterdata', params: { resource: 'teams' } },
      },
      {
        key: 'md-users',
        permission: 'users',
        label: 'masterdata.resources.users',
        icon: Users,
        to: { name: 'masterdata', params: { resource: 'users' } },
      },
      {
        key: 'md-roles',
        superuser: true,
        label: 'masterdata.resources.roles',
        icon: ShieldCheck,
        to: { name: 'masterdata', params: { resource: 'roles' } },
      },
      {
        key: 'md-numberSequences',
        permission: 'number_sequences',
        label: 'masterdata.resources.numberSequences',
        icon: Hash,
        to: { name: 'masterdata', params: { resource: 'numberSequences' } },
      },
    ],
  },
  {
    key: 'administration',
    label: 'nav.administration',
    superuser: true,
    items: [
      { key: 'settings', label: 'nav.settings', icon: SlidersHorizontal, to: { name: 'settings' } },
    ],
  },
]

/** Which menu entry is active for a route (detail pages highlight their list). */
export function activeKey(name: string | undefined, params: Record<string, unknown>): string {
  switch (name) {
    case 'asset':
      return 'assets'
    case 'license':
      return 'licenses'
    case 'reservation':
      return 'reservations'
    case 'order':
      return 'orders'
    case 'portal-request':
      return 'portal-requests'
    case 'portal-approval':
      return 'portal-approvals'
    case 'portal-device':
      return 'portal-devices'
    case 'settings-ldap':
      return 'settings'
    case 'masterdata':
      return `md-${params.resource}`
    default:
      return name ?? ''
  }
}
