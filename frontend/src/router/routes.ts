import type { RouteRecordRaw } from 'vue-router'
import type { Schemas } from '@/api/types'

declare module 'vue-router' {
  interface RouteMeta {
    /** Accessible without login. */
    public?: boolean
    /** Restricted to the IT department. */
    it?: boolean
    /** Restricted to administrators (superusers). */
    superuser?: boolean
    /** Restricted to department approvers. */
    approver?: boolean
    /** Area the user's roles must allow reading. */
    permission?: Schemas['ResourceKey']
    /** Pickup terminal pages (terminal account and IT staff). */
    terminal?: boolean
    /** i18n key of the page title. */
    title?: string
    /** Module that can be switched off in the site settings. */
    module?: Schemas['ModuleKey']
    /** Settings section a sub-page belongs to (highlighted in the settings menu). */
    section?: string
  }
}

export const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'login',
    component: () => import('@/views/auth/LoginView.vue'),
    meta: { public: true, title: 'auth.signIn' },
  },
  {
    path: '/terminal',
    component: () => import('@/layouts/TerminalLayout.vue'),
    meta: { terminal: true },
    children: [
      {
        path: '',
        name: 'terminal',
        component: () => import('@/views/terminal/TerminalListView.vue'),
        meta: { module: 'terminal', terminal: true, title: 'terminal.title' },
      },
      {
        path: ':id([0-9a-f-]{36})',
        name: 'terminal-pickup',
        component: () => import('@/views/terminal/TerminalPickupView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { module: 'terminal', terminal: true, title: 'terminal.title' },
      },
    ],
  },
  {
    path: '/requests/:id([0-9a-f-]{36})/protocol',
    name: 'handover-protocol',
    component: () => import('@/views/requests/HandoverProtocolView.vue'),
    props: (route) => ({ id: String(route.params.id) }),
    meta: { permission: 'requests', it: true, title: 'handover.protocol' },
  },
  {
    path: '/',
    component: () => import('@/layouts/AppLayout.vue'),
    children: [
      {
        path: '',
        name: 'dashboard',
        component: () => import('@/views/DashboardView.vue'),
        meta: { title: 'nav.dashboard' },
      },
      // Employee self-service
      {
        path: 'portal/new',
        name: 'portal-new',
        component: () => import('@/views/portal/NewRequestView.vue'),
        meta: { title: 'nav.newRequest' },
      },
      {
        path: 'portal/requests',
        name: 'portal-requests',
        component: () => import('@/views/portal/MyRequestsView.vue'),
        meta: { title: 'nav.myRequests' },
      },
      {
        path: 'portal/requests/:id([0-9a-f-]{36})',
        name: 'portal-request',
        component: () => import('@/views/portal/MyRequestDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { title: 'nav.myRequests' },
      },
      {
        path: 'portal/approvals',
        name: 'portal-approvals',
        component: () => import('@/views/portal/ApprovalsView.vue'),
        meta: { approver: true, title: 'nav.approvals' },
      },
      {
        path: 'portal/approvals/:id([0-9a-f-]{36})',
        name: 'portal-approval',
        component: () => import('@/views/portal/ApprovalDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { approver: true, title: 'nav.approvals' },
      },
      {
        path: 'profile/appearance',
        name: 'profile-appearance',
        component: () => import('@/views/profile/AppearanceSettingsView.vue'),
        meta: { title: 'profile.appearance.title' },
      },
      {
        path: 'profile/notifications',
        name: 'profile-notifications',
        component: () => import('@/views/profile/NotificationSettingsView.vue'),
        meta: { title: 'profile.notifications.title' },
      },
      {
        path: 'profile/security',
        name: 'profile-security',
        component: () => import('@/views/profile/SecuritySettingsView.vue'),
        meta: { title: 'profile.security.title' },
      },
      {
        path: 'portal/devices',
        name: 'portal-devices',
        component: () => import('@/views/portal/MyDevicesView.vue'),
        meta: { title: 'nav.myDevices' },
      },
      {
        path: 'portal/software',
        name: 'portal-licenses',
        component: () => import('@/views/portal/MyLicensesView.vue'),
        meta: { module: 'licenses', title: 'nav.mySoftware' },
      },
      {
        path: 'portal/issues',
        name: 'portal-issues',
        component: () => import('@/views/portal/MyIssuesView.vue'),
        meta: { module: 'issues', title: 'nav.myIssues' },
      },
      {
        path: 'portal/issues/:id([0-9a-f-]{36})',
        name: 'portal-issue',
        component: () => import('@/views/issues/IssueDetailView.vue'),
        props: (route) => ({ id: String(route.params.id), viewer: 'reporter' }),
        meta: { module: 'issues', title: 'nav.myIssues' },
      },
      {
        path: 'portal/devices/:id([0-9a-f-]{36})',
        name: 'portal-device',
        component: () => import('@/views/portal/MyDeviceDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { title: 'nav.myDevices' },
      },
      // IT: planning
      {
        path: 'calendar',
        name: 'calendar',
        component: () => import('@/views/calendar/CalendarView.vue'),
        meta: { permission: 'requests', module: 'calendar', it: true, title: 'nav.calendar' },
      },
      // IT: inventory
      {
        path: 'inventory/assets',
        name: 'assets',
        component: () => import('@/views/inventory/AssetListView.vue'),
        meta: { permission: 'assets', it: true, title: 'nav.assets' },
      },
      {
        path: 'inventory/assets/:id([0-9a-f-]{36})',
        name: 'asset',
        component: () => import('@/views/inventory/AssetDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { permission: 'assets', it: true, title: 'nav.assets' },
      },
      {
        path: 'inventory/consumables',
        name: 'consumables',
        component: () => import('@/views/inventory/ConsumableListView.vue'),
        meta: {
          permission: 'consumables',
          module: 'consumables',
          it: true,
          title: 'nav.consumables',
        },
      },
      {
        path: 'inventory/licenses',
        name: 'licenses',
        component: () => import('@/views/inventory/LicenseListView.vue'),
        meta: { permission: 'licenses', module: 'licenses', it: true, title: 'nav.licenses' },
      },
      {
        path: 'inventory/licenses/:id([0-9a-f-]{36})',
        name: 'license',
        component: () => import('@/views/inventory/LicenseDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { permission: 'licenses', module: 'licenses', it: true, title: 'nav.licenses' },
      },
      {
        path: 'inventory/issues',
        name: 'issues',
        component: () => import('@/views/inventory/IssueListView.vue'),
        meta: { permission: 'issues', module: 'issues', it: true, title: 'nav.issues' },
      },
      {
        path: 'inventory/issues/:id([0-9a-f-]{36})',
        name: 'issue',
        component: () => import('@/views/issues/IssueDetailView.vue'),
        props: (route) => ({ id: String(route.params.id), viewer: 'it' }),
        meta: { permission: 'issues', module: 'issues', it: true, title: 'nav.issues' },
      },
      // Former name of the consumables page; keeps old bookmarks working.
      { path: 'inventory/stock', redirect: (to) => ({ name: 'consumables', query: to.query }) },
      {
        path: 'inventory/log',
        name: 'event-log',
        component: () => import('@/views/inventory/EventLogView.vue'),
        meta: { permission: 'assets', it: true, title: 'nav.eventLog' },
      },
      // IT: requests
      {
        path: 'requests',
        name: 'requests',
        component: () => import('@/views/requests/RequestListView.vue'),
        meta: { permission: 'requests', it: true, title: 'nav.requests' },
      },
      {
        path: 'requests/:id([0-9a-f-]{36})',
        name: 'request',
        component: () => import('@/views/requests/RequestDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { permission: 'requests', it: true, title: 'nav.requests' },
      },
      // IT: procurement
      {
        path: 'procurement/needs',
        name: 'needs',
        component: () => import('@/views/procurement/NeedsView.vue'),
        meta: { permission: 'procurement', module: 'procurement', it: true, title: 'nav.needs' },
      },
      {
        path: 'procurement/orders',
        name: 'orders',
        component: () => import('@/views/procurement/OrderListView.vue'),
        meta: { permission: 'procurement', module: 'procurement', it: true, title: 'nav.orders' },
      },
      {
        path: 'procurement/orders/:id([0-9a-f-]{36})',
        name: 'order',
        component: () => import('@/views/procurement/OrderDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { permission: 'procurement', module: 'procurement', it: true, title: 'nav.orders' },
      },
      // IT: master data
      {
        path: 'masterdata/:resource',
        name: 'masterdata',
        component: () => import('@/views/masterdata/MasterDataView.vue'),
        props: true,
        meta: { it: true, title: 'nav.masterdata' },
      },
      // Administration
      {
        path: 'settings',
        component: () => import('@/views/settings/SettingsView.vue'),
        meta: { superuser: true },
        children: [
          { path: '', name: 'settings', redirect: { name: 'settings-features' } },
          {
            path: 'features',
            name: 'settings-features',
            component: () => import('@/views/settings/FeatureSettingsView.vue'),
            meta: { superuser: true, title: 'settings.sections.features' },
          },
          {
            path: 'rules',
            name: 'settings-rules',
            component: () => import('@/views/settings/RulesSettingsView.vue'),
            meta: { superuser: true, title: 'settings.sections.rules' },
          },
          {
            path: 'mail',
            name: 'settings-mail',
            component: () => import('@/views/settings/MailSettingsView.vue'),
            meta: { superuser: true, title: 'settings.sections.mail' },
          },
          {
            path: 'notifications',
            name: 'settings-notifications',
            component: () => import('@/views/settings/SiteNotificationsView.vue'),
            meta: { superuser: true, title: 'settings.sections.notifications' },
          },
          {
            path: 'ldap',
            name: 'settings-ldap',
            component: () => import('@/views/settings/LdapSettingsView.vue'),
            meta: { superuser: true, title: 'settings.sections.ldap' },
          },
          {
            path: 'ldap/sync',
            name: 'settings-ldap-sync',
            component: () => import('@/views/settings/LdapSyncView.vue'),
            meta: { superuser: true, title: 'settings.ldap.sync.title', section: 'settings-ldap' },
          },
        ],
      },
      {
        path: ':pathMatch(.*)*',
        name: 'not-found',
        component: () => import('@/views/NotFoundView.vue'),
      },
    ],
  },
]
