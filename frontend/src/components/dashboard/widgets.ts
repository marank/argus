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
import type { Schemas } from '@/api/types'
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

import type { Tone } from '@/utils/status'

/** One key figure in a panel; `key` is what the user's layout stores when it is switched off. */
export interface StatCardDef {
  key: string
  label: string
  labelArgs?: (rules: Schemas['RulesSchema']) => Record<string, unknown>
  icon: Component
  value: (data: Schemas['ITOverviewOut']) => number
  tone?: (data: Schemas['ITOverviewOut']) => Tone
  alert?: (data: Schemas['ITOverviewOut']) => boolean
  to?: RouteLocationRaw
  /** Shown only while this module or feature is on. */
  flag?: Schemas['FlagKey']
  /** Shown only while the user's roles allow reading this area. */
  permission?: Schemas['ResourceKey']
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
  size: Schemas['WidgetSize']
  /** Off until the user adds it from the widget list. */
  optional?: boolean
  /**
   * Can be added more than once, each with its own settings and title, e.g.
   * the week once for the counter and once for procurement.
   */
  multiple?: boolean
  /** Only offered while this module or feature is on. */
  flag?: Schemas['FlagKey']
  /** Only offered while the user's roles allow reading this area. */
  permission?: Schemas['ResourceKey']
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
        permission: 'requests',
        label: 'dashboard.assignedToMe',
        icon: UserRound,
        value: (d) => d.requests_mine,
        tone: () => 'primary',
        to: { name: 'requests', query: { assigned: 'me' } },
      },
      {
        key: 'my_teams',
        permission: 'requests',
        label: 'dashboard.myTeams',
        icon: UsersRound,
        value: (d) => d.requests_my_teams,
        tone: () => 'info',
        to: { name: 'requests', query: { assigned: 'my_teams' } },
      },
      {
        key: 'unassigned',
        permission: 'requests',
        label: 'dashboard.unassigned',
        icon: UserRoundX,
        value: (d) => d.requests_unassigned,
        tone: (d) => warnIf(d.requests_unassigned),
        to: { name: 'requests', query: { assigned: 'nobody' } },
      },
      {
        key: 'issues_mine',
        permission: 'issues',
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
        key: 'to_confirm',
        permission: 'requests',
        label: 'dashboard.toConfirm',
        icon: ClipboardCheck,
        value: (d) => d.requests_submitted,
        tone: () => 'warning',
        alert: (d) => !!d.requests_submitted,
        to: { name: 'requests', query: { status: 'submitted' } },
      },
      {
        key: 'to_prepare',
        permission: 'requests',
        label: 'dashboard.toPrepare',
        icon: PackageOpen,
        value: (d) => d.requests_to_prepare,
        tone: () => 'primary',
        to: { name: 'requests', query: { status: 'confirmed' } },
      },
      {
        key: 'ready',
        permission: 'requests',
        label: 'dashboard.readyForPickup',
        icon: PackageCheck,
        value: (d) => d.requests_ready,
        tone: () => 'success',
        to: { name: 'requests', query: { status: 'ready' } },
      },
      {
        key: 'overdue',
        permission: 'requests',
        label: 'dashboard.overdue',
        icon: AlarmClock,
        value: (d) => d.requests_overdue,
        tone: (d) => (d.requests_overdue ? 'error' : 'default'),
        alert: (d) => !!d.requests_overdue,
        to: { name: 'requests', query: { overdue: '1' } },
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
        permission: 'procurement',
        label: 'dashboard.ordersToPlace',
        icon: ShoppingCart,
        value: (d) => d.orders_to_place,
        to: { name: 'orders', query: { status: 'draft' } },
        flag: 'procurement',
      },
      {
        key: 'orders_in_transit',
        permission: 'procurement',
        label: 'dashboard.ordersInTransit',
        icon: Truck,
        value: (d) => d.orders_in_transit,
        tone: () => 'info',
        to: { name: 'orders', query: { status: 'ordered' } },
        flag: 'procurement',
      },
      {
        key: 'below_minimum',
        permission: 'consumables',
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
        permission: 'issues',
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
        permission: 'licenses',
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
        permission: 'assets',
        label: 'dashboard.warrantyExpiring',
        labelArgs: (rules) => ({ days: rules.warranty_warning_days }),
        icon: ShieldAlert,
        value: (d) => d.warranty_expiring,
      },
    ],
  },
  {
    id: 'asset_status',
    permission: 'assets',
    description: 'dashboard.widgets.assetStatus',
    title: 'dashboard.devicesByStatus',
    icon: ChartBar,
    size: 'large',
    component: AssetStatusWidget,
  },
  {
    id: 'upcoming',
    permission: 'requests',
    description: 'dashboard.widgets.upcoming',
    title: 'dashboard.upcoming',
    icon: CalendarDays,
    size: 'medium',
    multiple: true,
    component: UpcomingWidget,
  },
  {
    id: 'activity',
    permission: 'assets',
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
    permission: 'requests',
    title: 'dashboard.widgets.overdueReturns.title',
    description: 'dashboard.widgets.overdueReturns.description',
    icon: AlarmClock,
    size: 'medium',
    optional: true,
    component: OverdueReturnsWidget,
  },
  {
    id: 'week',
    permission: 'requests',
    title: 'dashboard.widgets.week.title',
    description: 'dashboard.widgets.week.description',
    icon: CalendarRange,
    size: 'large',
    optional: true,
    multiple: true,
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
    permission: 'requests',
    title: 'dashboard.widgets.requestTrend.title',
    description: 'dashboard.widgets.requestTrend.description',
    icon: TrendingUp,
    size: 'medium',
    optional: true,
    component: RequestTrendWidget,
  },
  {
    id: 'due_returns',
    permission: 'requests',
    title: 'dashboard.widgets.dueReturns.title',
    description: 'dashboard.widgets.dueReturns.description',
    icon: Undo2,
    size: 'medium',
    optional: true,
    multiple: true,
    component: DueReturnsWidget,
  },
  {
    id: 'waiting',
    permission: 'requests',
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
    permission: 'consumables',
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
    permission: 'procurement',
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
    multiple: true,
    component: ShortcutsWidget,
  },
  {
    id: 'notes',
    title: 'dashboard.widgets.notes.title',
    description: 'dashboard.widgets.notes.description',
    icon: NotebookPen,
    size: 'small',
    optional: true,
    multiple: true,
    component: NotesWidget,
  },
]

/** Cards whose module or feature is on and whose area the user may read. */
export const availableCards = (
  def: WidgetDef,
  isOn: (flag: Schemas['FlagKey']) => boolean,
  can: (permission: Schemas['ResourceKey']) => boolean,
) =>
  (def.cards ?? []).filter(
    (card) => (!card.flag || isOn(card.flag)) && (!card.permission || can(card.permission)),
  )

/** What the layout functions need to know of a widget. */
type LayoutDef = Pick<WidgetDef, 'id' | 'size' | 'optional' | 'multiple'>

export const defaultLayout = (defs: LayoutDef[]): Schemas['DashboardWidgetOut'][] =>
  defs.map((d) => ({
    id: d.id,
    widget: null,
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
export function mergeOrder(
  defaults: string[],
  saved: string[],
  known: (id: string) => boolean = (id) => defaults.includes(id),
): string[] {
  const order = saved.filter((id, index) => known(id) && saved.indexOf(id) === index)
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

/**
 * The kind of widget an entry shows. The first instance of a widget has the
 * widget's id; further ones (`multiple`) have their own id and name the widget.
 */
export const widgetType = (widget: Pick<Schemas['DashboardWidgetOut'], 'id' | 'widget'>) =>
  widget.widget ?? widget.id

/** Another instance of a widget that allows several, with its default size. */
export function newInstance(def: LayoutDef): Schemas['DashboardWidgetOut'] {
  return {
    ...defaultLayout([def])[0]!,
    id: `${def.id}~${Math.random().toString(36).slice(2, 8)}`,
    widget: def.id,
    visible: true,
  }
}

/** The user's saved layout applied to the widgets that exist (see `mergeOrder`). */
export function resolveLayout(
  defs: LayoutDef[],
  saved: Schemas['DashboardWidgetOut'][] | undefined,
): Schemas['DashboardWidgetOut'][] {
  if (!saved?.length) return defaultLayout(defs)
  const ids = defs.map((d) => d.id)
  // Further instances stay as long as their widget exists and allows several.
  const isCopyOf = (w: Schemas['DashboardWidgetOut']) =>
    !!w.widget && w.widget !== w.id && !!defs.find((d) => d.id === w.widget)?.multiple
  return mergeOrder(
    ids,
    saved.map((w) => w.id),
    (id) => ids.includes(id) || saved.some((w) => w.id === id && isCopyOf(w)),
  ).map((id) => {
    const widget = saved.find((w) => w.id === id)
    if (!widget) return defaultLayout(defs.filter((d) => d.id === id))[0]!
    return {
      ...widget,
      // A copy whose widget no longer allows several shows as the first instance.
      widget: isCopyOf(widget) ? widget.widget : null,
      hidden_cards: [...widget.hidden_cards],
      card_order: [...widget.card_order],
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
export const isDefaultLayout = (defs: LayoutDef[], layout: Schemas['DashboardWidgetOut'][]) =>
  JSON.stringify(layout) === JSON.stringify(defaultLayout(defs))
