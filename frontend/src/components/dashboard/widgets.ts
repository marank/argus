import {
  AlarmClock,
  Activity,
  CalendarClock,
  CalendarDays,
  CalendarRange,
  CalendarX,
  ChartBar,
  CircleAlert,
  ClipboardCheck,
  ClipboardList,
  Boxes,
  Hourglass,
  KeyRound,
  ListTodo,
  MessageSquareWarning,
  NotebookPen,
  PackageCheck,
  PackageMinus,
  PackageOpen,
  ShieldAlert,
  ShoppingCart,
  TrendingUp,
  Truck,
  Undo2,
  UserRound,
  UserRoundX,
  UsersRound,
  Zap,
} from '@lucide/vue'
import type { Component } from 'vue'
import type { RouteLocationRaw } from 'vue-router'

import ActivityWidget from '@/components/dashboard/widgets/ActivityWidget.vue'
import AssetStatusWidget from '@/components/dashboard/widgets/AssetStatusWidget.vue'
import DueReturnsWidget from '@/components/dashboard/widgets/DueReturnsWidget.vue'
import ExpiringWidget from '@/components/dashboard/widgets/ExpiringWidget.vue'
import LowStockWidget from '@/components/dashboard/widgets/LowStockWidget.vue'
import MyTasksWidget from '@/components/dashboard/widgets/MyTasksWidget.vue'
import NotesWidget from '@/components/dashboard/widgets/NotesWidget.vue'
import OpenOrdersWidget from '@/components/dashboard/widgets/OpenOrdersWidget.vue'
import OverdueReturnsWidget from '@/components/dashboard/widgets/OverdueReturnsWidget.vue'
import RequestTrendWidget from '@/components/dashboard/widgets/RequestTrendWidget.vue'
import ShortcutsWidget from '@/components/dashboard/widgets/ShortcutsWidget.vue'
import TeamLoadWidget from '@/components/dashboard/widgets/TeamLoadWidget.vue'
import UpcomingWidget from '@/components/dashboard/widgets/UpcomingWidget.vue'
import WaitingRequestsWidget from '@/components/dashboard/widgets/WaitingRequestsWidget.vue'
import WeekWidget from '@/components/dashboard/widgets/WeekWidget.vue'
import type { WidgetSettings, WidgetSize } from '@/types/accounts'
import type { ITOverview } from '@/types/dashboard'
import type { FlagKey, Rules } from '@/types/settings'
import type { Tone } from '@/utils/status'

/** One key figure in a panel; `key` is what the user's layout stores when it is switched off. */
export interface StatCardDef {
  key: string
  label: string
  labelArgs?: (rules: Rules) => Record<string, unknown>
  icon: Component
  value: (data: ITOverview) => number
  tone?: (data: ITOverview) => Tone
  alert?: (data: ITOverview) => boolean
  to?: RouteLocationRaw
  /** Shown only while this module or feature is on. */
  flag?: FlagKey
}

/**
 * A block on the IT dashboard: either a panel of key figures (`cards`) or its
 * own component. Components get the overview as `data` and their stored
 * `options`; they emit `update:options` to change them (e.g. the notes text).
 */
export interface WidgetDef {
  id: string
  title: string
  /** One line for the widget list in the editor. */
  description: string
  icon: Component
  size: WidgetSize
  /** Off until the user adds it from the widget list. */
  optional?: boolean
  /** Only offered while this module or feature is on. */
  flag?: FlagKey
  cards?: StatCardDef[]
  component?: Component
}

const warnIf = (n: number): Tone => (n ? 'warning' : 'default')

/** All widgets in their default order. New ones join existing layouts at this position. */
export const WIDGETS: WidgetDef[] = [
  {
    // The viewer's own queue: open requests and reports by who is responsible.
    id: 'mine',
    description: 'dashboard.widgets.mine',
    title: 'dashboard.groups.mine',
    icon: UserRound,
    size: 'large',
    cards: [
      {
        key: 'assigned_to_me',
        label: 'dashboard.assignedToMe',
        icon: UserRound,
        value: (d) => d.requests_mine,
        tone: () => 'primary',
        to: { name: 'reservations', query: { assigned: 'me' } },
      },
      {
        key: 'my_teams',
        label: 'dashboard.myTeams',
        icon: UsersRound,
        value: (d) => d.requests_my_teams,
        tone: () => 'info',
        to: { name: 'reservations', query: { assigned: 'my_teams' } },
      },
      {
        key: 'unassigned',
        label: 'dashboard.unassigned',
        icon: UserRoundX,
        value: (d) => d.requests_unassigned,
        tone: (d) => warnIf(d.requests_unassigned),
        to: { name: 'reservations', query: { assigned: 'nobody' } },
      },
      {
        key: 'issues_mine',
        label: 'dashboard.issuesMine',
        icon: MessageSquareWarning,
        value: (d) => d.issues_mine,
        tone: (d) => warnIf(d.issues_mine),
        to: { name: 'issues', query: { assigned: 'me' } },
        flag: 'issues',
      },
    ],
  },
  {
    id: 'requests',
    description: 'dashboard.widgets.requests',
    title: 'dashboard.groups.requests',
    icon: ClipboardList,
    size: 'large',
    cards: [
      {
        key: 'to_approve',
        label: 'dashboard.toApprove',
        icon: ClipboardCheck,
        value: (d) => d.reservations_submitted,
        tone: () => 'warning',
        alert: (d) => !!d.reservations_submitted,
        to: { name: 'reservations', query: { status: 'submitted' } },
      },
      {
        key: 'to_prepare',
        label: 'dashboard.toPrepare',
        icon: PackageOpen,
        value: (d) => d.reservations_to_prepare,
        tone: () => 'primary',
        to: { name: 'reservations', query: { status: 'approved' } },
      },
      {
        key: 'ready',
        label: 'dashboard.readyForPickup',
        icon: PackageCheck,
        value: (d) => d.reservations_ready,
        tone: () => 'success',
        to: { name: 'reservations', query: { status: 'ready' } },
      },
      {
        key: 'overdue',
        label: 'dashboard.overdue',
        icon: AlarmClock,
        value: (d) => d.reservations_overdue,
        tone: (d) => (d.reservations_overdue ? 'error' : 'default'),
        alert: (d) => !!d.reservations_overdue,
        to: { name: 'reservations', query: { overdue: '1' } },
      },
    ],
  },
  {
    id: 'stock',
    description: 'dashboard.widgets.stock',
    title: 'dashboard.groups.stock',
    icon: Boxes,
    size: 'medium',
    cards: [
      {
        key: 'orders_to_place',
        label: 'dashboard.ordersToPlace',
        icon: ShoppingCart,
        value: (d) => d.orders_to_place,
        to: { name: 'orders', query: { status: 'draft' } },
        flag: 'procurement',
      },
      {
        key: 'orders_in_transit',
        label: 'dashboard.ordersInTransit',
        icon: Truck,
        value: (d) => d.orders_in_transit,
        tone: () => 'info',
        to: { name: 'orders', query: { status: 'ordered' } },
        flag: 'procurement',
      },
      {
        key: 'below_minimum',
        label: 'dashboard.belowMinimum',
        icon: CircleAlert,
        value: (d) => d.low_consumables,
        tone: (d) => warnIf(d.low_consumables),
        alert: (d) => !!d.low_consumables,
        to: { name: 'consumables', query: { below_minimum: '1' } },
        flag: 'consumables',
      },
    ],
  },
  {
    id: 'attention',
    description: 'dashboard.widgets.attention',
    title: 'dashboard.groups.attention',
    icon: CalendarClock,
    size: 'medium',
    cards: [
      {
        key: 'open_issues',
        label: 'dashboard.openIssues',
        icon: MessageSquareWarning,
        value: (d) => d.open_issues,
        tone: (d) => warnIf(d.open_issues),
        alert: (d) => !!d.open_issues,
        to: { name: 'issues' },
        flag: 'issues',
      },
      {
        key: 'licenses_expiring',
        label: 'dashboard.licensesExpiring',
        labelArgs: (rules) => ({ days: rules.license_warning_days }),
        icon: KeyRound,
        value: (d) => d.licenses_expiring,
        tone: (d) => warnIf(d.licenses_expiring),
        to: { name: 'licenses', query: { expiring: '1' } },
        flag: 'licenses',
      },
      {
        key: 'warranty_expiring',
        label: 'dashboard.warrantyExpiring',
        labelArgs: (rules) => ({ days: rules.warranty_warning_days }),
        icon: ShieldAlert,
        value: (d) => d.warranty_expiring,
      },
    ],
  },
  {
    id: 'asset_status',
    description: 'dashboard.widgets.assetStatus',
    title: 'dashboard.devicesByStatus',
    icon: ChartBar,
    size: 'large',
    component: AssetStatusWidget,
  },
  {
    id: 'upcoming',
    description: 'dashboard.widgets.upcoming',
    title: 'dashboard.upcoming',
    icon: CalendarDays,
    size: 'medium',
    component: UpcomingWidget,
  },
  {
    id: 'activity',
    description: 'dashboard.widgets.activity',
    title: 'dashboard.recentActivity',
    icon: Activity,
    size: 'medium',
    component: ActivityWidget,
  },
  {
    id: 'my_tasks',
    title: 'dashboard.widgets.myTasks.title',
    description: 'dashboard.widgets.myTasks.description',
    icon: ListTodo,
    size: 'medium',
    optional: true,
    component: MyTasksWidget,
  },
  {
    id: 'overdue_returns',
    title: 'dashboard.widgets.overdueReturns.title',
    description: 'dashboard.widgets.overdueReturns.description',
    icon: AlarmClock,
    size: 'medium',
    optional: true,
    component: OverdueReturnsWidget,
  },
  {
    id: 'week',
    title: 'dashboard.widgets.week.title',
    description: 'dashboard.widgets.week.description',
    icon: CalendarRange,
    size: 'large',
    optional: true,
    component: WeekWidget,
  },
  {
    id: 'team_load',
    title: 'dashboard.widgets.teamLoad.title',
    description: 'dashboard.widgets.teamLoad.description',
    icon: UsersRound,
    size: 'medium',
    optional: true,
    component: TeamLoadWidget,
  },
  {
    id: 'request_trend',
    title: 'dashboard.widgets.requestTrend.title',
    description: 'dashboard.widgets.requestTrend.description',
    icon: TrendingUp,
    size: 'medium',
    optional: true,
    component: RequestTrendWidget,
  },
  {
    id: 'due_returns',
    title: 'dashboard.widgets.dueReturns.title',
    description: 'dashboard.widgets.dueReturns.description',
    icon: Undo2,
    size: 'medium',
    optional: true,
    component: DueReturnsWidget,
  },
  {
    id: 'waiting',
    title: 'dashboard.widgets.waiting.title',
    description: 'dashboard.widgets.waiting.description',
    icon: Hourglass,
    size: 'medium',
    optional: true,
    component: WaitingRequestsWidget,
  },
  {
    id: 'expiring',
    title: 'dashboard.widgets.expiring.title',
    description: 'dashboard.widgets.expiring.description',
    icon: CalendarX,
    size: 'medium',
    optional: true,
    component: ExpiringWidget,
  },
  {
    id: 'low_stock',
    title: 'dashboard.widgets.lowStock.title',
    description: 'dashboard.widgets.lowStock.description',
    icon: PackageMinus,
    size: 'small',
    optional: true,
    flag: 'consumables',
    component: LowStockWidget,
  },
  {
    id: 'open_orders',
    title: 'dashboard.widgets.openOrders.title',
    description: 'dashboard.widgets.openOrders.description',
    icon: Truck,
    size: 'medium',
    optional: true,
    flag: 'procurement',
    component: OpenOrdersWidget,
  },
  {
    id: 'shortcuts',
    title: 'dashboard.widgets.shortcuts.title',
    description: 'dashboard.widgets.shortcuts.description',
    icon: Zap,
    size: 'small',
    optional: true,
    component: ShortcutsWidget,
  },
  {
    id: 'notes',
    title: 'dashboard.widgets.notes.title',
    description: 'dashboard.widgets.notes.description',
    icon: NotebookPen,
    size: 'small',
    optional: true,
    component: NotesWidget,
  },
]

/** Cards whose module or feature is on. */
export const availableCards = (def: WidgetDef, isOn: (flag: FlagKey) => boolean) =>
  (def.cards ?? []).filter((card) => !card.flag || isOn(card.flag))

/** What the layout functions need to know of a widget. */
type LayoutDef = Pick<WidgetDef, 'id' | 'size' | 'optional'>

export const defaultLayout = (defs: LayoutDef[]): WidgetSettings[] =>
  defs.map((d) => ({
    id: d.id,
    visible: !d.optional,
    size: d.size,
    height: 'auto',
    hidden_cards: [],
    card_order: [],
    options: {},
  }))

/**
 * A saved order applied to the ids that exist: unknown ids are dropped, ids
 * added since join behind their default predecessor.
 */
export function mergeOrder(defaults: string[], saved: string[]): string[] {
  const order = saved.filter((id, index) => defaults.includes(id) && saved.indexOf(id) === index)
  defaults.forEach((id, index) => {
    if (order.includes(id)) return
    const before = defaults
      .slice(0, index)
      .reverse()
      .find((d) => order.includes(d))
    order.splice(before ? order.indexOf(before) + 1 : 0, 0, id)
  })
  return order
}

/** `id` takes the place of `target`; the ones in between shift by one. */
export function moveBefore(order: string[], id: string, target: string): string[] {
  const from = order.indexOf(id)
  const to = order.indexOf(target)
  if (from < 0 || to < 0 || from === to) return order
  const moved = order.filter((x) => x !== id)
  moved.splice(to, 0, id)
  return moved
}

/** The user's saved layout applied to the widgets that exist (see `mergeOrder`). */
export function resolveLayout(
  defs: LayoutDef[],
  saved: WidgetSettings[] | undefined,
): WidgetSettings[] {
  if (!saved?.length) return defaultLayout(defs)
  return mergeOrder(
    defs.map((d) => d.id),
    saved.map((w) => w.id),
  ).map((id) => {
    const widget = saved.find((w) => w.id === id)
    if (!widget) return defaultLayout(defs.filter((d) => d.id === id))[0]!
    // Every field in a fixed order, filled in for layouts saved before it existed.
    return {
      id: widget.id,
      visible: widget.visible,
      size: widget.size,
      height: widget.height ?? 'auto',
      hidden_cards: [...(widget.hidden_cards ?? [])],
      card_order: [...(widget.card_order ?? [])],
      options: { ...widget.options },
    }
  })
}

/** Cards in the order the user gave them. */
export const orderCards = (cards: StatCardDef[], order: string[]) =>
  mergeOrder(
    cards.map((c) => c.key),
    order,
  ).map((key) => cards.find((c) => c.key === key)!)

/** Whether a layout is the default one, so nothing needs to be stored. */
export const isDefaultLayout = (defs: LayoutDef[], layout: WidgetSettings[]) =>
  JSON.stringify(layout) === JSON.stringify(defaultLayout(defs))
