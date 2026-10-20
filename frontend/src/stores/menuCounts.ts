import { defineStore } from 'pinia'
import { ref } from 'vue'

import { portalApi } from '@/api/reservations'
import type { MenuCounts } from '@/types/reservations'

/** Numbers for the self-service menu; pages refresh them when they change what they count. */
export const useMenuCountsStore = defineStore('menuCounts', () => {
  const counts = ref<MenuCounts | null>(null)

  async function refresh() {
    try {
      counts.value = await portalApi.menuCounts()
    } catch {
      // The badges are a hint; the pages themselves show the truth.
    }
  }

  return { counts, refresh }
})
