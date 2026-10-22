import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi, isChallenge } from '@/api/auth'
import { ApiError } from '@/api/client'
import { setLocale } from '@/i18n'
import type {
  CurrentUser,
  PermissionKey,
  PermissionLevel,
  TwoFactorChallenge,
} from '@/types/accounts'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<CurrentUser | null>(null)
  const checked = ref(false)

  const isAuthenticated = computed(() => user.value !== null)
  const isItStaff = computed(() => user.value?.is_it_staff ?? false)
  const isSuperuser = computed(() => user.value?.is_superuser ?? false)
  const isTerminal = computed(() => user.value?.is_terminal ?? false)
  const isApprover = computed(() => user.value?.is_approver ?? false)

  /** Whether the user's roles allow reading (or with `write`, changing) an area. */
  function can(resource: PermissionKey, level: PermissionLevel = 'read'): boolean {
    const granted = user.value?.permissions?.[resource]
    return level === 'read' ? !!granted : granted === 'write'
  }

  function apply(current: CurrentUser | null) {
    user.value = current
    if (current) setLocale(current.language)
  }

  async function fetchCurrentUser() {
    try {
      apply(await authApi.me())
    } catch (error) {
      // Anything but "not logged in" is unexpected; show the login page either way.
      if (!(error instanceof ApiError) || error.status !== 401) console.error(error)
      user.value = null
    } finally {
      checked.value = true
    }
  }

  /** Returns the challenge when the second sign-in step is due, else null. */
  async function login(username: string, password: string): Promise<TwoFactorChallenge | null> {
    const result = await authApi.login(username, password)
    if (isChallenge(result)) return result
    apply(result)
    return null
  }

  async function verifyLogin(code: string) {
    apply(await authApi.verifyLogin(code))
  }

  async function logout() {
    await authApi.logout()
    user.value = null
  }

  async function changeNotifications(
    settings: Pick<CurrentUser, 'notification_settings' | 'app_notification_settings'>,
  ) {
    if (user.value) user.value = await authApi.updatePreferences(settings)
  }

  async function changeDashboard(settings: CurrentUser['dashboard_settings']) {
    if (user.value) user.value = await authApi.updatePreferences({ dashboard_settings: settings })
  }

  async function changeLanguage(language: 'en' | 'de') {
    setLocale(language)
    if (user.value) user.value = await authApi.updatePreferences({ language })
  }

  return {
    user,
    checked,
    isAuthenticated,
    isItStaff,
    isSuperuser,
    isTerminal,
    isApprover,
    can,
    fetchCurrentUser,
    login,
    verifyLogin,
    logout,
    changeLanguage,
    changeNotifications,
    changeDashboard,
    clear: () => (user.value = null),
  }
})
