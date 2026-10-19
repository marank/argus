import type { RouteRecordRaw } from 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    /** Accessible without login. */
    public?: boolean
    /** Restricted to the IT department. */
    it?: boolean
    /** Pickup terminal pages (terminal account and IT staff). */
    terminal?: boolean
    /** i18n key of the page title. */
    title?: string
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
        meta: { terminal: true, title: 'terminal.title' },
      },
      {
        path: ':id([0-9a-f-]{36})',
        name: 'terminal-pickup',
        component: () => import('@/views/terminal/TerminalPickupView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { terminal: true, title: 'terminal.title' },
      },
    ],
  },
  {
    path: '/reservations/:id([0-9a-f-]{36})/protocol',
    name: 'handover-protocol',
    component: () => import('@/views/reservations/HandoverProtocolView.vue'),
    props: (route) => ({ id: String(route.params.id) }),
    meta: { it: true, title: 'handover.protocol' },
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
        path: 'portal/devices',
        name: 'portal-devices',
        component: () => import('@/views/portal/MyDevicesView.vue'),
        meta: { title: 'nav.myDevices' },
      },
      // IT: inventory
      {
        path: 'inventory/assets',
        name: 'assets',
        component: () => import('@/views/inventory/AssetListView.vue'),
        meta: { it: true, title: 'nav.assets' },
      },
      {
        path: 'inventory/assets/:id([0-9a-f-]{36})',
        name: 'asset',
        component: () => import('@/views/inventory/AssetDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { it: true, title: 'nav.assets' },
      },
      {
        path: 'inventory/stock',
        name: 'stock',
        component: () => import('@/views/inventory/StockListView.vue'),
        meta: { it: true, title: 'nav.stock' },
      },
      {
        path: 'inventory/log',
        name: 'event-log',
        component: () => import('@/views/inventory/EventLogView.vue'),
        meta: { it: true, title: 'nav.eventLog' },
      },
      // IT: reservations
      {
        path: 'reservations',
        name: 'reservations',
        component: () => import('@/views/reservations/ReservationListView.vue'),
        meta: { it: true, title: 'nav.reservations' },
      },
      {
        path: 'reservations/:id([0-9a-f-]{36})',
        name: 'reservation',
        component: () => import('@/views/reservations/ReservationDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { it: true, title: 'nav.reservations' },
      },
      // IT: procurement
      {
        path: 'procurement/needs',
        name: 'needs',
        component: () => import('@/views/procurement/NeedsView.vue'),
        meta: { it: true, title: 'nav.needs' },
      },
      {
        path: 'procurement/orders',
        name: 'orders',
        component: () => import('@/views/procurement/OrderListView.vue'),
        meta: { it: true, title: 'nav.orders' },
      },
      {
        path: 'procurement/orders/:id([0-9a-f-]{36})',
        name: 'order',
        component: () => import('@/views/procurement/OrderDetailView.vue'),
        props: (route) => ({ id: String(route.params.id) }),
        meta: { it: true, title: 'nav.orders' },
      },
      // IT: master data
      {
        path: 'masterdata/:resource',
        name: 'masterdata',
        component: () => import('@/views/masterdata/MasterDataView.vue'),
        props: true,
        meta: { it: true, title: 'nav.masterdata' },
      },
      {
        path: ':pathMatch(.*)*',
        name: 'not-found',
        component: () => import('@/views/NotFoundView.vue'),
      },
    ],
  },
]
