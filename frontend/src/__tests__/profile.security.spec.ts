import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import SecuritySettingsView from '@/views/profile/SecuritySettingsView.vue'

import { makeUser } from './helpers'
import { button, click, typeInto } from './dom'
import { mountView, pageText } from './layoutHelpers'

const api = vi.hoisted(() => ({
  status: vi.fn<() => Promise<unknown>>(),
  setup: vi.fn<(method: string, password: string) => Promise<unknown>>(),
  resendSetupCode: vi.fn<() => Promise<unknown>>(),
  confirm: vi.fn<(code: string) => Promise<unknown>>(),
  renewBackupCodes: vi.fn<(password: string) => Promise<unknown>>(),
  disable: vi.fn<(password: string) => Promise<unknown>>(),
  me: vi.fn<() => Promise<unknown>>(),
}))
vi.mock('@/api/auth', async (importOriginal) => {
  const { me, ...twoFactorApi } = api
  return {
    ...(await importOriginal<typeof import('@/api/auth')>()),
    twoFactorApi,
    authApi: { me },
  }
})

const status = (fields: Partial<Schemas['TwoFactorStatusOut']> = {}) => ({
  method: null,
  backup_codes_left: 0,
  email_available: true,
  email_hint: 'j***@example.com',
  ...fields,
})

const SETUP: Schemas['TwoFactorSetupOut'] = {
  method: 'totp',
  secret: 'JBSWY3DPEHPK3PXP',
  qr_svg: 'data:image/svg+xml;base64,PHN2Zy8+',
  uri: 'otpauth://totp/Argus:jdoe?secret=JBSWY3DPEHPK3PXP',
  code_sent: false,
  email_hint: '',
}
const CODES = ['aaaa-bbbb-cccc', 'dddd-eeee-ffff']

const passwordField = () =>
  [...document.body.querySelectorAll<HTMLInputElement>('.n-modal input[type="password"]')].at(-1)!

async function enterCode(code: string) {
  const first = document.body.querySelector<HTMLInputElement>('.code-input input')!
  await typeInto(first, code)
}

/** The setup or confirm button of the method row labelled `method`. */
function methodButton(method: string) {
  const row = [...document.body.querySelectorAll('.setting-row')].find(
    (r) => r.querySelector('.label')?.textContent?.trim() === method,
  )!
  return row.querySelector('button')
}

describe('sign-in security', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
    api.status.mockResolvedValue(status())
    api.me.mockResolvedValue(makeUser())
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    vi.useRealTimers()
  })

  async function page() {
    const result = await mountView(SecuritySettingsView)
    unmount = () => result.wrapper.unmount()
    return result
  }

  describe('status', () => {
    it('offers both methods while two-factor sign-in is off', async () => {
      await page()
      expect(pageText()).toContain('Inactive')
      expect(methodButton('Authenticator app')?.textContent?.trim()).toBe('Set up')
      expect(methodButton('Code by email')?.textContent?.trim()).toBe('Set up')
      expect(pageText()).not.toContain('Backup codes')
    })

    it('explains why codes by email are not available', async () => {
      api.status.mockResolvedValue(status({ email_available: false }))
      await page()
      expect(pageText()).toContain('no email address on file or email delivery disabled')
      expect(methodButton('Code by email')?.disabled).toBe(true)
    })

    it('shows the method in use, the codes left and a switch to the other one', async () => {
      api.status.mockResolvedValue(status({ method: 'totp', backup_codes_left: 8 }))
      await page()
      expect(pageText()).toContain('Active · Authenticator app')
      expect(methodButton('Authenticator app')).toBeNull()
      expect(methodButton('Code by email')?.textContent?.trim()).toBe('Switch')
      expect(pageText()).toContain('8 backup codes available')
      expect(pageText()).not.toContain('Only 8 backup codes')
    })

    it('warns when few backup codes are left', async () => {
      api.status.mockResolvedValue(status({ method: 'email', backup_codes_left: 2 }))
      await page()
      expect(pageText()).toContain('Only 2 backup codes available.')
    })

    it('says so when the status cannot be loaded', async () => {
      api.status.mockRejectedValue(new ApiError(500, 'HTTP 500'))
      await page()
      expect(pageText()).toContain('An error occurred')
    })
  })

  describe('setting up the app', () => {
    async function startTotp() {
      await page()
      await click(methodButton('Authenticator app')!)
      expect(pageText()).toContain('Set up an authenticator app')
      expect(button('Next').disabled).toBe(true)
      await typeInto(passwordField(), 'secret')
      await click('Next')
    }

    it('asks for the password, then shows the QR code and the key', async () => {
      api.setup.mockResolvedValue(SETUP)
      await startTotp()
      expect(api.setup).toHaveBeenCalledWith('totp', 'secret')
      const qr = document.body.querySelector<HTMLImageElement>('.qr img')!
      expect(qr.getAttribute('src')).toBe(SETUP.qr_svg)
      expect(qr.alt).toBe('QR code for the authenticator app')
      expect(document.body.querySelector('.secret code')?.textContent).toBe('JBSW Y3DP EHPK 3PXP')
    })

    it('stays at the password when it is wrong', async () => {
      api.setup.mockRejectedValue(new ApiError(400, 'Wrong password.'))
      await startTotp()
      expect(pageText()).toContain('Wrong password.')
      expect(document.body.querySelector('.code-input')).toBeNull()
    })

    it('switches on with the first code and shows the backup codes once', async () => {
      api.setup.mockResolvedValue(SETUP)
      api.confirm.mockResolvedValue({ backup_codes: CODES })
      await startTotp()
      api.status.mockResolvedValue(status({ method: 'totp', backup_codes_left: 2 }))
      await enterCode('123456')
      expect(api.confirm).toHaveBeenCalledWith('123456')
      expect(pageText()).toContain('Two-factor authentication is active.')
      const shown = [...document.body.querySelectorAll('.codes li')].map((li) => li.textContent)
      expect(shown).toEqual(CODES)
      // Switched on already: the page and the signed-in user are reloaded.
      expect(pageText()).toContain('Active · Authenticator app')
      expect(api.me).toHaveBeenCalledOnce()

      expect(button('Done').disabled).toBe(true)
      await click(document.body.querySelector('.stored')!)
      await click('Done')
      // Opened again, the dialog starts over: the codes are not shown a second time.
      await click(methodButton('Code by email')!)
      expect(pageText()).toContain('Set up codes by email')
      expect(document.body.querySelector('.codes')).toBeNull()
    })

    it('clears a wrong code and lets the user try again', async () => {
      api.setup.mockResolvedValue(SETUP)
      api.confirm.mockRejectedValue(new ApiError(400, 'Wrong code.'))
      await startTotp()
      await enterCode('123456')
      expect(pageText()).toContain('Wrong code.')
      const boxes = [...document.body.querySelectorAll<HTMLInputElement>('.code-input input')]
      expect(boxes.map((b) => b.value).join('')).toBe('')
      expect(api.status).toHaveBeenCalledOnce()
    })

    it('starts over when the setup expired', async () => {
      api.setup.mockResolvedValue(SETUP)
      api.confirm.mockRejectedValue(new ApiError(409, 'The setup has expired. Start again.'))
      await startTotp()
      await enterCode('123456')
      expect(pageText()).toContain('The setup has expired. Start again.')
      expect(document.body.querySelector('.code-input')).toBeNull()
      expect(passwordField().value).toBe('')
    })
  })

  describe('setting up codes by email', () => {
    async function startEmail() {
      await page()
      await click(methodButton('Code by email')!)
      expect(pageText()).toContain('Set up codes by email')
      await typeInto(passwordField(), 'secret')
      await click('Next')
    }

    it('names where the code went and allows resending after a while', async () => {
      vi.useFakeTimers()
      const sent = { ...SETUP, method: 'email', code_sent: true, email_hint: 'j***@example.com' }
      api.setup.mockResolvedValue(sent)
      api.resendSetupCode.mockResolvedValue(sent)
      await startEmail()
      expect(api.setup).toHaveBeenCalledWith('email', 'secret')
      expect(pageText()).toContain('A 6-digit code has been sent to j***@example.com.')
      expect(document.body.querySelector('.qr')).toBeNull()
      expect(button('Send again in 30 s').disabled).toBe(true)

      await vi.advanceTimersByTimeAsync(30_000)
      await click('Send code again')
      expect(api.resendSetupCode).toHaveBeenCalledOnce()
      expect(pageText()).toContain('Send again in 30 s')
    })

    it('says when the code could not be sent', async () => {
      api.setup.mockResolvedValue({ ...SETUP, method: 'email', code_sent: false })
      await startEmail()
      expect(pageText()).toContain('The code could not be sent.')
    })
  })

  describe('backup codes', () => {
    beforeEach(() => {
      api.status.mockResolvedValue(status({ method: 'totp', backup_codes_left: 1 }))
    })

    it('renews them with the password and shows the new ones', async () => {
      api.renewBackupCodes.mockResolvedValue({ backup_codes: CODES })
      await page()
      await click('Generate new codes')
      expect(pageText()).toContain('Ten new backup codes will be generated')
      api.status.mockResolvedValue(status({ method: 'totp', backup_codes_left: 10 }))
      await typeInto(passwordField(), 'secret')
      await click(button('Generate new codes'))
      expect(api.renewBackupCodes).toHaveBeenCalledWith('secret')
      const shown = [...document.body.querySelectorAll('.codes li')].map((li) => li.textContent)
      expect(shown).toEqual(CODES)
      expect(pageText()).toContain('10 backup codes available')
    })

    it('keeps the old codes when the password is wrong', async () => {
      api.renewBackupCodes.mockRejectedValue(new ApiError(400, 'Wrong password.'))
      await page()
      await click('Generate new codes')
      await typeInto(passwordField(), 'wrong')
      await click(button('Generate new codes'))
      expect(pageText()).toContain('Wrong password.')
      expect(document.body.querySelector('.codes')).toBeNull()
    })

    it('copies them to the clipboard', async () => {
      const writeText = vi.fn<(text: string) => Promise<void>>().mockResolvedValue()
      Object.defineProperty(navigator, 'clipboard', { value: { writeText }, configurable: true })
      api.renewBackupCodes.mockResolvedValue({ backup_codes: CODES })
      await page()
      await click('Generate new codes')
      await typeInto(passwordField(), 'secret')
      await click(button('Generate new codes'))
      await click('Copy')
      expect(writeText).toHaveBeenCalledWith('aaaa-bbbb-cccc\ndddd-eeee-ffff')
      expect(pageText()).toContain('Copied to the clipboard')
    })
  })

  it('switches two-factor sign-in off with the password', async () => {
    api.status.mockResolvedValue(status({ method: 'totp', backup_codes_left: 5 }))
    api.disable.mockResolvedValue(undefined)
    await page()
    await click('Disable two-factor authentication')
    api.status.mockResolvedValue(status())
    await typeInto(passwordField(), 'secret')
    await click(button('Disable two-factor authentication'))
    expect(api.disable).toHaveBeenCalledWith('secret')
    expect(pageText()).toContain('Two-factor authentication disabled')
    expect(pageText()).toContain('Inactive')
  })
})
