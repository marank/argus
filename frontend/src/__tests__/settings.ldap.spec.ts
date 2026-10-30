import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import LdapSettingsView from '@/views/settings/LdapSettingsView.vue'

import { makeUser } from './helpers'
import { button, click, typeInto } from './dom'
import { mountView, pageText } from './layoutHelpers'

const api = vi.hoisted(() => ({
  get: vi.fn<() => Promise<unknown>>(),
  update: vi.fn<(data: Schemas['LdapSettingsIn']) => Promise<unknown>>(),
  test: vi.fn<(data: Record<string, unknown>) => Promise<unknown>>(),
}))
vi.mock('@/api/settings', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/settings')>()),
  ldapSettingsApi: api,
}))

function ldap(fields: Partial<Schemas['LdapSettingsOut']> = {}): Schemas['LdapSettingsOut'] {
  return {
    enabled: true,
    server_uri: 'ldaps://dc1.example.com',
    start_tls: false,
    verify_cert: true,
    ca_cert_file: '',
    timeout: 5,
    bind_dn: 'CN=svc-argus,DC=example,DC=com',
    bind_password_set: true,
    user_search_base: 'OU=Staff,DC=example,DC=com',
    user_filter: '(sAMAccountName={username})',
    attr_username: 'sAMAccountName',
    attr_first_name: 'givenName',
    attr_last_name: 'sn',
    attr_employee_number: '',
    attr_email: 'mail',
    attr_job_title: '',
    attr_phone: '',
    create_users: true,
    locked: [],
    env_names: {},
    ...fields,
  }
}

/** What the form sends for `ldap()` unchanged, without the bind password. */
const { bind_password_set: _set, locked: _locked, env_names: _env, ...SENT } = ldap()

const input = (placeholder: string) =>
  document.body.querySelector<HTMLInputElement>(`input[placeholder="${placeholder}"]`)!
const serverInput = () => input('ldaps://dc1.example.com')
const passwordInput = () => document.body.querySelector<HTMLInputElement>('input[type="password"]')!

describe('LDAP settings', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
    api.get.mockResolvedValue(ldap())
    api.update.mockImplementation(async (data) => ldap({ ...data }))
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
  })

  async function page() {
    const result = await mountView(LdapSettingsView, {
      user: makeUser({ is_it_staff: true, is_superuser: true }),
    })
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('shows the stored values and keeps the password hidden', async () => {
    await page()
    expect(pageText()).toContain('Active')
    expect(serverInput().value).toBe('ldaps://dc1.example.com')
    expect(passwordInput().value).toBe('')
    expect(passwordInput().placeholder).toBe('Stored – leave empty to keep')
    expect(pageText()).not.toContain('You have unsaved changes.')
  })

  it('locks fields set by environment variables', async () => {
    api.get.mockResolvedValue(
      ldap({
        locked: ['server_uri', 'bind_password'],
        env_names: { server_uri: 'LDAP_SERVER_URI', bind_password: 'LDAP_BIND_PASSWORD' },
      }),
    )
    await page()
    expect(pageText()).toContain('Some values come from environment variables (2)')
    expect(serverInput().disabled).toBe(true)
    expect(passwordInput().disabled).toBe(true)
    expect(input('OU=Staff,DC=example,DC=com').disabled).toBe(false)
    expect(
      document.body.querySelector('[aria-label="Set by environment variable LDAP_SERVER_URI"]'),
    ).not.toBeNull()
    // A password from the environment cannot be removed here either.
    expect(pageText()).not.toContain('Remove stored password')
  })

  describe('saving', () => {
    it('sends the changed values without the stored password', async () => {
      await page()
      await typeInto(serverInput(), 'ldaps://dc2.example.com')
      expect(pageText()).toContain('You have unsaved changes.')
      await click('Save')
      expect(api.update).toHaveBeenCalledWith({
        ...SENT,
        server_uri: 'ldaps://dc2.example.com',
        bind_password: null,
      })
      expect(pageText()).not.toContain('You have unsaved changes.')
    })

    it('sends a new password', async () => {
      await page()
      await typeInto(passwordInput(), 's3cret')
      await click('Save')
      expect(api.update).toHaveBeenCalledWith({ ...SENT, bind_password: 's3cret' })
    })

    it('removes the stored password when asked', async () => {
      await page()
      await click(
        [...document.body.querySelectorAll('.n-checkbox')].find((c) =>
          c.textContent?.includes('Remove stored password'),
        )!,
      )
      expect(passwordInput().disabled).toBe(true)
      await click('Save')
      expect(api.update).toHaveBeenCalledWith({ ...SENT, bind_password: '' })
    })

    it('needs server, search base, filter and username attribute while enabled', async () => {
      await page()
      await typeInto(input('OU=Staff,DC=example,DC=com'), '')
      expect(button('Save').disabled).toBe(true)
    })

    it('resets the form to the stored values', async () => {
      await page()
      await typeInto(serverInput(), 'ldaps://typo')
      await click('Reset')
      expect(serverInput().value).toBe('ldaps://dc1.example.com')
      expect(pageText()).not.toContain('You have unsaved changes.')
      expect(api.update).not.toHaveBeenCalled()
    })

    it('shows why saving failed and keeps the changes', async () => {
      api.update.mockRejectedValue(new ApiError(400, 'Server URI must start with ldap://'))
      await page()
      await typeInto(serverInput(), 'dc2.example.com')
      await click('Save')
      expect(pageText()).toContain('Server URI must start with ldap://')
      expect(serverInput().value).toBe('dc2.example.com')
    })
  })

  describe('connection test', () => {
    it('tests the unsaved values and shows what would be taken over', async () => {
      api.test.mockResolvedValue({
        server: 'ldaps://dc2.example.com',
        user: {
          dn: 'CN=Jane Doe,OU=Staff,DC=example,DC=com',
          first_name: 'Jane',
          last_name: 'Doe',
          username: 'jdoe',
          email: '',
        },
      })
      await page()
      await typeInto(serverInput(), 'ldaps://dc2.example.com')
      await typeInto(input('Username (optional)'), '  jdoe ')
      await click('Test connection')
      expect(api.test).toHaveBeenCalledWith({
        ...SENT,
        server_uri: 'ldaps://dc2.example.com',
        bind_password: null,
        username: 'jdoe',
      })
      const text = pageText()
      expect(text).toContain('Connected to ldaps://dc2.example.com')
      expect(text).toContain('Entry found')
      const rows = [...document.body.querySelectorAll('dl.result dt')].map((dt) => [
        dt.textContent,
        dt.nextElementSibling?.textContent,
      ])
      expect(rows).toEqual([
        ['DN', 'CN=Jane Doe,OU=Staff,DC=example,DC=com'],
        ['First name', 'Jane'],
        ['Last name', 'Doe'],
        ['Email', '—'],
        ['Username', 'jdoe'],
      ])
    })

    it('shows only the connection without a username', async () => {
      api.test.mockResolvedValue({ server: 'ldaps://dc1.example.com', user: null })
      await page()
      await click('Test connection')
      expect(pageText()).toContain('Connected to ldaps://dc1.example.com')
      expect(pageText()).not.toContain('Entry found')
    })

    it('shows why the connection failed', async () => {
      api.test.mockRejectedValue(new ApiError(400, 'Invalid credentials (bind DN)'))
      await page()
      await click('Test connection')
      expect(pageText()).toContain('Invalid credentials (bind DN)')
      expect(pageText()).not.toContain('Connected to')
    })

    it('needs a server', async () => {
      await page()
      await typeInto(serverInput(), '')
      expect(button('Test connection').disabled).toBe(true)
    })
  })

  describe('user sync', () => {
    it('opens on the saved, enabled configuration', async () => {
      const { router } = await page()
      await click('Sync users')
      expect(router.currentRoute.value.name).toBe('settings-ldap-sync')
    })

    it('waits for unsaved changes to be saved', async () => {
      await page()
      await typeInto(serverInput(), 'ldaps://dc2.example.com')
      expect(button('Sync users').disabled).toBe(true)
    })

    it('needs LDAP to be enabled', async () => {
      api.get.mockResolvedValue(ldap({ enabled: false }))
      await page()
      expect(pageText()).toContain('Inactive')
      expect(button('Sync users').disabled).toBe(true)
    })
  })
})
