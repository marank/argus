import { flushPromises, mount } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { ApiError } from '@/api/client'
import { i18n } from '@/i18n'
import LoginView from '@/views/auth/LoginView.vue'

import { makeUser } from './helpers'

const api = vi.hoisted(() => ({
  health: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  login: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  verifyLogin: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
  resendLoginCode: vi.fn<(...args: unknown[]) => Promise<unknown>>(),
}))

vi.mock('@/api/auth', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/auth')>()),
  authApi: api,
}))

const emailChallenge = (fields: Record<string, unknown> = {}) => ({
  two_factor: 'email',
  code_sent: true,
  email_hint: 'j***@example.com',
  ...fields,
})

async function mountLogin(url = '/login') {
  const pinia = createPinia()
  setActivePinia(pinia)
  const page = { render: () => null }
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      { path: '/login', component: LoginView },
      { path: '/', name: 'dashboard', component: page },
      { path: '/profile', component: page },
    ],
  })
  await router.push(url)
  const wrapper = mount(LoginView, {
    attachTo: document.body,
    global: { plugins: [i18n, pinia, router] },
  })
  await flushPromises()
  return { wrapper, router }
}

describe('LoginView', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
    api.health.mockResolvedValue({ status: 'ok' })
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    vi.useRealTimers()
  })

  async function login(url?: string) {
    const result = await mountLogin(url)
    unmount = () => result.wrapper.unmount()
    return result
  }

  async function signIn(wrapper: Awaited<ReturnType<typeof mountLogin>>['wrapper']) {
    const [username, password] = wrapper.findAll('input')
    await username!.setValue('jdoe')
    await password!.setValue('secret')
    await wrapper.find('form').trigger('submit')
    await flushPromises()
  }

  async function typeCode(
    wrapper: Awaited<ReturnType<typeof mountLogin>>['wrapper'],
    code: string,
  ) {
    const first = wrapper.find('.code-input input').element as HTMLInputElement
    first.value = code
    first.dispatchEvent(new Event('input'))
    await flushPromises()
  }

  const submitButton = (wrapper: Awaited<ReturnType<typeof mountLogin>>['wrapper']) =>
    wrapper.find('button[type="submit"]').element as HTMLButtonElement

  it('only lets a filled form be sent', async () => {
    const { wrapper } = await login()
    expect(submitButton(wrapper).disabled).toBe(true)
    await wrapper.findAll('input')[0]!.setValue('jdoe')
    await wrapper.findAll('input')[1]!.setValue('secret')
    expect(submitButton(wrapper).disabled).toBe(false)
  })

  it('signs in and goes back to the page asked for', async () => {
    api.login.mockResolvedValue(makeUser())
    const { wrapper, router } = await login('/login?next=/profile')
    await signIn(wrapper)
    expect(api.login).toHaveBeenCalledWith('jdoe', 'secret')
    expect(router.currentRoute.value.fullPath).toBe('/profile')
  })

  it('goes to the start page without a way back', async () => {
    api.login.mockResolvedValue(makeUser())
    const { wrapper, router } = await login()
    await signIn(wrapper)
    expect(router.currentRoute.value.fullPath).toBe('/')
  })

  it('shows why the sign-in failed', async () => {
    api.login.mockRejectedValue(new ApiError(401, 'Wrong username or password.'))
    const { wrapper } = await login()
    await signIn(wrapper)
    expect(wrapper.text()).toContain('Wrong username or password.')
  })

  it('tells when the server is down instead of an error', async () => {
    api.health.mockRejectedValue(new ApiError(503, ''))
    const { wrapper } = await login()
    expect(wrapper.text()).toContain('Argus is not reachable right now')
    expect(wrapper.text()).toContain('SYS · OFFLINE')

    api.login.mockRejectedValue(new ApiError(0, 'Connection lost'))
    await signIn(wrapper)
    expect(wrapper.text()).not.toContain('Connection lost')

    api.login.mockResolvedValue(makeUser())
    await signIn(wrapper)
    expect(wrapper.text()).toContain('SYS · ONLINE')
  })

  it('says when the session expired', async () => {
    const { wrapper } = await login('/login?expired=1')
    expect(wrapper.text()).toContain('Your session has expired')
  })

  it('asks for the app code as second step and signs in once it is complete', async () => {
    api.login.mockResolvedValue({ two_factor: 'totp', code_sent: false, email_hint: '' })
    api.verifyLogin.mockResolvedValue(makeUser())
    const { wrapper, router } = await login('/login?next=/profile')
    await signIn(wrapper)
    expect(wrapper.text()).toContain('Confirm sign-in')
    expect(wrapper.text()).toContain('authenticator app')
    await typeCode(wrapper, '123456')
    expect(api.verifyLogin).toHaveBeenCalledWith('123456')
    expect(router.currentRoute.value.fullPath).toBe('/profile')
  })

  it('clears a wrong code and stays on the second step', async () => {
    api.login.mockResolvedValue({ two_factor: 'totp', code_sent: false, email_hint: '' })
    api.verifyLogin.mockRejectedValue(new ApiError(400, 'Wrong code.'))
    const { wrapper } = await login()
    await signIn(wrapper)
    await typeCode(wrapper, '123456')
    expect(wrapper.text()).toContain('Wrong code.')
    expect(wrapper.text()).toContain('Confirm sign-in')
    const boxes = wrapper
      .findAll('.code-input input')
      .map((b) => (b.element as HTMLInputElement).value)
    expect(boxes.join('')).toBe('')
  })

  it('goes back to the password when the challenge expired', async () => {
    api.login.mockResolvedValue({ two_factor: 'totp', code_sent: false, email_hint: '' })
    api.verifyLogin.mockRejectedValue(new ApiError(429, 'Too many attempts.'))
    const { wrapper } = await login()
    await signIn(wrapper)
    await typeCode(wrapper, '123456')
    expect(wrapper.text()).toContain('Too many attempts.')
    expect(wrapper.text()).toContain('Sign in to Argus')
  })

  it('names the address the email code went to and allows resending after a while', async () => {
    vi.useFakeTimers()
    api.login.mockResolvedValue(emailChallenge())
    api.resendLoginCode.mockResolvedValue(emailChallenge())
    const { wrapper } = await login()
    await signIn(wrapper)
    expect(wrapper.text()).toContain('sent to j***@example.com')
    expect(wrapper.text()).toContain('Send again in 30 s')

    await vi.advanceTimersByTimeAsync(30_000)
    const resend = wrapper.findAll('button').find((b) => b.text() === 'Send code again')!
    await resend.trigger('click')
    await flushPromises()
    expect(api.resendLoginCode).toHaveBeenCalledOnce()
    expect(wrapper.text()).toContain('Send again in 30 s')
  })

  it('offers backup codes when the email could not be sent', async () => {
    api.login.mockResolvedValue(emailChallenge({ code_sent: false }))
    api.verifyLogin.mockResolvedValue(makeUser())
    const { wrapper } = await login()
    await signIn(wrapper)
    expect(wrapper.text()).toContain('could not be sent by email')
    expect(wrapper.text()).toContain('Backup code')
    expect(wrapper.find('.code-input').exists()).toBe(false)

    const input = wrapper.find('input')
    await input.setValue('abcd-efgh')
    expect(submitButton(wrapper).disabled).toBe(true)
    await input.setValue('abcd-efgh-ijkl')
    expect(submitButton(wrapper).disabled).toBe(false)
    await wrapper.find('form').trigger('submit')
    await flushPromises()
    expect(api.verifyLogin).toHaveBeenCalledWith('abcd-efgh-ijkl')
  })

  it('switches between code and backup code', async () => {
    api.login.mockResolvedValue({ two_factor: 'totp', code_sent: false, email_hint: '' })
    const { wrapper } = await login()
    await signIn(wrapper)
    const toggle = () => wrapper.findAll('button').find((b) => /Use a/.test(b.text()))!
    await toggle().trigger('click')
    expect(wrapper.text()).toContain('backup codes')
    await toggle().trigger('click')
    expect(wrapper.find('.code-input').exists()).toBe(true)
  })

  it('goes back to the password form', async () => {
    api.login.mockResolvedValue({ two_factor: 'totp', code_sent: false, email_hint: '' })
    const { wrapper } = await login()
    await signIn(wrapper)
    await wrapper
      .findAll('button')
      .find((b) => b.text() === 'Back')!
      .trigger('click')
    expect(wrapper.text()).toContain('Sign in to Argus')
    expect((wrapper.findAll('input')[1]!.element as HTMLInputElement).value).toBe('')
  })
})
