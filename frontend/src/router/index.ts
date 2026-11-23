import { createRouter, createWebHistory, type RouteLocationNormalized } from 'vue-router'

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

/** Whether a signed-in user (not the terminal) may open the page. */
function mayOpen(
  to: RouteLocationNormalized,
  auth: ReturnType<typeof useAuthStore>,
  features: ReturnType<typeof useFeaturesStore>,
): boolean {
  if ((to.meta.it || to.meta.terminal) && !auth.isItStaff) return false
  if (to.meta.permission && !auth.can(to.meta.permission, to.meta.write ? 'write' : 'read')) {
    return false
  }
  if (to.meta.approver && !auth.isApprover) return false
  if (to.meta.superuser && !auth.isSuperuser) return false
  // Pages of modules switched off in the site settings are not reachable.
  return !to.meta.module || features.isOn(to.meta.module)
}

/** The login page, coming back to `to` afterwards. */
const loginFor = (to: RouteLocationNormalized) => ({
  name: 'login',
  query: to.fullPath !== '/' ? { next: to.fullPath } : {},
})

router.beforeEach(async (to) => {
  const auth = useAuthStore()
  if (!auth.checked) await auth.fetchCurrentUser()

  if (to.meta.public) {
    const signedIn = auth.isAuthenticated && to.name === 'login'
    return signedIn ? { name: auth.isTerminal ? 'terminal' : 'dashboard' } : true
  }
  if (!auth.isAuthenticated) return loginFor(to)
  const features = useFeaturesStore()
  if (!features.settings) await features.load().catch(() => undefined)
  // The shared terminal account only ever sees the pickup terminal.
  if (auth.isTerminal) {
    return to.meta.terminal ? true : { name: 'terminal' }
  }
  return mayOpen(to, auth, features) ? true : { name: 'dashboard' }
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
  if (!current.meta.public) void router.push(loginFor(current))
})

export default router
