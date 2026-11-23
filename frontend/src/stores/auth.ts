import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi, isChallenge } from '@/api/auth'
import { ApiError } from '@/api/client'
import { setLocale } from '@/i18n'
import type { Schemas } from '@/api/types'
import { useTheme, type ThemeMode } from '@/theme/useTheme'

export const useAuthStore = defineStore('auth', () => {
  const { mode: themeMode } = useTheme()
  const user = ref<Schemas['CurrentUserOut'] | null>(null)
  const checked = ref(false)
  /** Why the last session ended, for the notice on the login page; reset by the next sign-in. */
  const endReason = ref<'signedOut' | 'expired' | null>(null)

  const isAuthenticated = computed(() => user.value !== null)
  const isItStaff = computed(() => user.value?.is_it_staff ?? false)
  const isSuperuser = computed(() => user.value?.is_superuser ?? false)
  const isTerminal = computed(() => user.value?.is_terminal ?? false)
  const isApprover = computed(() => user.value?.is_approver ?? false)

  /** Whether the user's roles allow reading (or with `write`, changing) an area. */
  function can(
    resource: Schemas['ResourceKey'],
    level: Schemas['PermissionLevel'] = 'read',
  ): boolean {
    const granted = user.value?.permissions[resource]
    return level === 'read' ? !!granted : granted === 'write'
  }

  function apply(current: Schemas['CurrentUserOut'] | null) {
    user.value = current
    if (current) {
      setLocale(current.language)
      themeMode.value = current.theme
      endReason.value = null
    }
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
  async function login(
    username: string,
    password: string,
  ): Promise<Schemas['TwoFactorChallengeOut'] | null> {
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
    endReason.value = 'signedOut'
  }

  /** The server no longer knows the session (a 401 on any call). */
  function expire() {
    user.value = null
    endReason.value = 'expired'
  }

  async function changeNotifications(
    settings: Pick<
      Schemas['CurrentUserOut'],
      'notification_settings' | 'app_notification_settings'
    >,
  ) {
    if (user.value) user.value = await authApi.updatePreferences(settings)
  }

  async function changeDashboard(settings: Schemas['CurrentUserOut']['dashboard_settings']) {
    if (user.value) user.value = await authApi.updatePreferences({ dashboard_settings: settings })
  }

  async function changeLanguage(language: 'en' | 'de') {
    setLocale(language)
    if (user.value) user.value = await authApi.updatePreferences({ language })
  }

  /** Shows the theme at once and keeps it in the profile, so it follows the user to other devices. */
  async function changeTheme(theme: ThemeMode) {
    themeMode.value = theme
    if (user.value) user.value = await authApi.updatePreferences({ theme })
  }

  return {
    user,
    checked,
    endReason,
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
    expire,
    changeLanguage,
    changeTheme,
    changeNotifications,
    changeDashboard,
    clear: () => (user.value = null),
  }
})
