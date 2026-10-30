import type { Schemas } from '@/api/types'

/** Props every dashboard widget component gets. */
export interface WidgetProps {
  data: Schemas['ITOverviewOut']
  /** The widget's own stored settings; changed by emitting `update:options`. */
  options: Record<string, unknown>
  /** The name the user gave this instance; the widget's own title when unset. */
  title?: string
}
