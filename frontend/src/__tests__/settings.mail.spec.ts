import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import MailSettingsView from '@/views/settings/MailSettingsView.vue'

import { makeSiteSettings, makeUser } from './helpers'
import { button, click, typeInto } from './dom'
import { mountView, pageText } from './layoutHelpers'

const api = vi.hoisted(() => ({
  get: vi.fn<() => Promise<unknown>>(),
  update: vi.fn<(data: Schemas['MailSettingsIn']) => Promise<unknown>>(),
  test: vi.fn<(to: string) => Promise<unknown>>(),
  site: vi.fn<() => Promise<unknown>>(),
}))
vi.mock('@/api/settings', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/settings')>()),
  mailSettingsApi: { get: api.get, update: api.update, test: api.test },
  siteSettingsApi: { get: api.site },
}))

const mail = (fields: Partial<Schemas['MailSettingsOut']> = {}): Schemas['MailSettingsOut'] => ({
  enabled: true,
  host: 'smtp.example.com',
  port: 587,
  security: 'starttls',
  username: 'argus',
  password_set: true,
  from_email: 'argus@example.com',
  from_name: 'Argus',
  app_url: 'https://argus.example.com',
  ...fields,
})

const SENT: Schemas['MailSettingsIn'] = {
  enabled: true,
  host: 'smtp.example.com',
  port: 587,
  security: 'starttls',
  username: 'argus',
  password: null,
  from_email: 'argus@example.com',
  from_name: 'Argus',
  app_url: 'https://argus.example.com',
}

const field = (placeholder: string) =>
  document.body.querySelector<HTMLInputElement>(`input[placeholder="${placeholder}"]`)!
const recipient = () => field('Recipient')

describe('mail settings', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
    api.get.mockResolvedValue(mail())
    api.update.mockImplementation(async (data) => mail({ ...data, password_set: true }))
    api.site.mockResolvedValue(makeSiteSettings({}, { mail_enabled: true }))
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
  })

  async function page() {
    const result = await mountView(MailSettingsView, {
      user: makeUser({ is_superuser: true, email: 'jane@example.com' }),
    })
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('shows the stored server without its password', async () => {
    await page()
    expect(field('smtp.example.com').value).toBe('smtp.example.com')
    const password = document.body.querySelector<HTMLInputElement>('input[type="password"]')!
    expect(password.value).toBe('')
    expect(password.placeholder).toBe('stored')
  })

  describe('saving', () => {
    it('keeps the stored password unless a new one is typed', async () => {
      await page()
      await typeInto(field('argus@example.com'), 'it@example.com')
      await click('Save')
      expect(api.update).toHaveBeenCalledWith({ ...SENT, from_email: 'it@example.com' })
    })

    it('sends a new password', async () => {
      await page()
      await typeInto(document.body.querySelector('input[type="password"]'), 'n3w')
      await click('Save')
      expect(api.update).toHaveBeenCalledWith({ ...SENT, password: 'n3w' })
    })

    it('reloads the site settings, which tell whether mail is on', async () => {
      await page()
      api.site.mockClear()
      await click('Save')
      expect(api.site).toHaveBeenCalledOnce()
    })

    it('shows what the server rejected and keeps the input', async () => {
      api.update.mockRejectedValue(
        new ApiError(422, 'from_email: value is not a valid email address'),
      )
      await page()
      await typeInto(field('argus@example.com'), 'not-an-address')
      await click('Save')
      expect(pageText()).toContain('from_email: value is not a valid email address')
      expect(field('argus@example.com').value).toBe('not-an-address')
    })
  })

  describe('test email', () => {
    it('goes to the signed-in user by default and reports the result', async () => {
      api.test.mockResolvedValue({ detail: 'Test email sent to jane@example.com.' })
      await page()
      expect(recipient().value).toBe('jane@example.com')
      await click('Send test email')
      expect(api.test).toHaveBeenCalledWith('jane@example.com')
      expect(pageText()).toContain('Test email sent to jane@example.com.')
    })

    it('goes to the address typed', async () => {
      api.test.mockResolvedValue({ detail: 'sent' })
      await page()
      await typeInto(recipient(), 'ops@example.com')
      await click('Send test email')
      expect(api.test).toHaveBeenCalledWith('ops@example.com')
    })

    it('shows why sending failed', async () => {
      api.test.mockRejectedValue(new ApiError(400, 'Connection refused by smtp.example.com'))
      await page()
      await click('Send test email')
      expect(pageText()).toContain('Connection refused by smtp.example.com')
    })

    it('needs a stored server and a recipient', async () => {
      api.get.mockResolvedValue(mail({ host: '' }))
      await page()
      expect(button('Send test email').disabled).toBe(true)
      unmount?.()
      document.body.innerHTML = ''

      api.get.mockResolvedValue(mail())
      await page()
      await typeInto(recipient(), '')
      expect(button('Send test email').disabled).toBe(true)
    })
  })
})
