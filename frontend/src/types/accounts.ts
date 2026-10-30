/** Areas of the app that roles grant rights on (see backend apps.accounts.permissions). */
export type PermissionKey =
  | 'models'
  | 'categories'
  | 'manufacturers'
  | 'suppliers'
  | 'locations'
  | 'departments'
  | 'teams'
  | 'users'
  | 'number_sequences'
  | 'requests'
  | 'assets'
  | 'consumables'
  | 'licenses'
  | 'issues'
  | 'procurement'
export type PermissionLevel = 'read' | 'write'

export type WidgetSize = 'small' | 'medium' | 'large'
/** `auto` fits the content and the row; the others are fixed heights that scroll. */
export type WidgetHeight = 'auto' | 'small' | 'medium' | 'large'

/** One dashboard widget as the user arranged it; the order of the list is the order on screen. */
export interface WidgetSettings {
  id: string
  /** Set on further instances of a widget: which widget it is (the first has its id). */
  widget?: string
  visible: boolean
  size: WidgetSize
  height: WidgetHeight
  /** Cards of a key figure panel the user switched off. */
  hidden_cards: string[]
  /** Cards of a key figure panel in the user's order; empty keeps the default order. */
  card_order: string[]
  /** The widget's own settings, such as the text of the notes widget. */
  options: Record<string, unknown>
}

/** The user's own dashboard layout (`dashboard_settings`); empty means the default. */
export interface DashboardSettings {
  widgets?: WidgetSettings[]
}
