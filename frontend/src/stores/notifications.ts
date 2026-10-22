import { defineStore } from 'pinia'
import { ref } from 'vue'

import { notificationsApi } from '@/api/notifications'

/** The number on the bell; the bell refreshes it on live signals and when opened. */
export const useNotificationsStore = defineStore('notifications', () => {
  const unread = ref(0)

  async function refresh() {
    try {
      unread.value = (await notificationsApi.unread()).unread
    } catch {
      // The number is a hint; the list itself shows the truth.
    }
  }

  return { unread, refresh }
})
