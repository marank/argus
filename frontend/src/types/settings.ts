import type { Schemas } from '@/api/types'

/** How a notification reaches someone: by email or in the app (the bell). */
export type NotificationChannel = keyof Pick<Schemas['NotificationSettingsOut'], 'mail' | 'app'>
