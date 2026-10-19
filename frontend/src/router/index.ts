import { createRouter, createWebHistory } from 'vue-router'

import { onUnauthorized } from '@/api/client'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'

import { routes } from './routes'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior: () => ({ top: 0 }),
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.checked) await auth.fetchCurrentUser()

  if (to.meta.public) {
    if (auth.isAuthenticated && to.name === 'login') {
      return { name: auth.isTerminal ? 'terminal' : 'dashboard' }
    }
    return true
  }
  if (!auth.isAuthenticated) {
    return { name: 'login', query: to.fullPath !== '/' ? { next: to.fullPath } : {} }
  }
  // The shared terminal account only ever sees the pickup terminal.
  if (auth.isTerminal) {
    return to.meta.terminal ? true : { name: 'terminal' }
  }
  if ((to.meta.it || to.meta.terminal) && !auth.isItStaff) {
    return { name: 'dashboard' }
  }
  return true
})

router.afterEach((to) => {
  const title = to.meta.title ? i18n.global.t(to.meta.title) : null
  document.title = title ? `${title} · Argus` : 'Argus'
})

// A 401 from any API call means the session expired: back to the login page.
onUnauthorized(() => {
  useAuthStore().clear()
  const current = router.currentRoute.value
  if (!current.meta.public) {
    router.push({ name: 'login', query: { next: current.fullPath, expired: '1' } })
  }
})

export default router
