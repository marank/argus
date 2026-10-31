import { createRouter, createWebHistory } from 'vue-router'

import { onUnauthorized } from '@/api/client'
import { i18n } from '@/i18n'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'

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
  const features = useFeaturesStore()
  if (!features.settings) await features.load().catch(() => undefined)
  // The shared terminal account only ever sees the pickup terminal.
  if (auth.isTerminal) {
    return to.meta.terminal ? true : { name: 'terminal' }
  }
  if ((to.meta.it || to.meta.terminal) && !auth.isItStaff) {
    return { name: 'dashboard' }
  }
  if (to.meta.permission && !auth.can(to.meta.permission)) {
    return { name: 'dashboard' }
  }
  if (to.meta.approver && !auth.isApprover) {
    return { name: 'dashboard' }
  }
  if (to.meta.superuser && !auth.isSuperuser) {
    return { name: 'dashboard' }
  }
  // Pages of modules switched off in the site settings are not reachable.
  if (to.meta.module && !features.isOn(to.meta.module)) {
    return { name: 'dashboard' }
  }
  return true
})

router.afterEach((to, _from, failure) => {
  // A navigation cancelled on the way (e.g. "keep editing") stays on the page and its title.
  if (failure) return
  const title = to.meta.title ? i18n.global.t(to.meta.title) : null
  document.title = title ? `${title} · Argus` : 'Argus'
})

// A 401 from any API call means the session expired: back to the login page, which
// says so. Calls still running after a sign-out answer 401 as well; they change nothing.
onUnauthorized(() => {
  const auth = useAuthStore()
  if (!auth.isAuthenticated) return
  auth.expire()
  const current = router.currentRoute.value
  if (!current.meta.public) {
    router.push({
      name: 'login',
      query: current.fullPath !== '/' ? { next: current.fullPath } : {},
    })
  }
})

export default router
