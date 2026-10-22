import type { Id } from './common'

/** A notification in the bell; title and text are in the user's language. */
export interface AppNotification {
  id: Id
  /** The notification kind (see NotificationKey), or one IT sent on purpose. */
  event: string
  title: string
  text: string
  /** The page it is about, e.g. "/portal/requests/<id>". */
  path: string
  read_at: string | null
  created_at: string
}
