import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import { useTheme } from '@/theme/useTheme'
import AppearanceSettingsView from '@/views/profile/AppearanceSettingsView.vue'

import { makeUser } from './helpers'
import { click } from './dom'
import { mountView } from './layoutHelpers'

const api = vi.hoisted(() => ({
  updatePreferences: vi.fn<(data: Record<string, unknown>) => Promise<unknown>>(),
}))
vi.mock('@/api/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/auth')>()),
  authApi: { updatePreferences: api.updatePreferences },
}))

const option = (theme: string) =>
  document.body.querySelector<HTMLElement>(`[data-theme-option="${theme}"]`)!

describe('own appearance settings', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    api.updatePreferences.mockReset()
    api.updatePreferences.mockImplementation(async (data) => makeUser(data))
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    useTheme().mode.value = 'system'
  })

  async function page(user = makeUser()) {
    const result = await mountView(AppearanceSettingsView, { user })
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('offers every theme, grouped into system, light and dark, and marks the current one', async () => {
    await page()
    const groups = [...document.body.querySelectorAll('[role="radiogroup"]')].map((group) => [
      group.getAttribute('aria-label'),
      [...group.querySelectorAll('[role="radio"]')].map((o) => o.textContent?.trim()),
    ])
    expect(groups).toEqual([
      ['System', ['System']],
      ['Light themes', ['Light', 'Solarized']],
      ['Dark themes', ['Dark', 'Retro']],
    ])
    expect(option('system').getAttribute('aria-checked')).toBe('true')
    // System previews light and dark side by side.
    expect(option('system').querySelectorAll('.half')).toHaveLength(2)
  })

  it('switches to the chosen theme and saves it in the profile', async () => {
    await page()
    await click(option('solarized'))
    expect(api.updatePreferences).toHaveBeenCalledWith({ theme: 'solarized' })
    expect(document.documentElement.dataset.theme).toBe('solarized')
    expect(option('solarized').getAttribute('aria-checked')).toBe('true')
  })

  it('shows the retro theme as a dark theme', async () => {
    await page()
    await click(option('retro'))
    expect(api.updatePreferences).toHaveBeenCalledWith({ theme: 'retro' })
    expect(document.documentElement.dataset.theme).toBe('retro')
    expect(useTheme().isDark.value).toBe(true)
  })

  it('does not save the theme that is already chosen', async () => {
    await page()
    await click(option('system'))
    expect(api.updatePreferences).not.toHaveBeenCalled()
  })

  it('reports when saving fails', async () => {
    api.updatePreferences.mockRejectedValue(new ApiError(500, 'Server error', {}))
    await page()
    await click(option('dark'))
    expect(document.body.textContent).toContain('An error occurred')
  })
})
