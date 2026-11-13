import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import type { Schemas } from '@/api/types'
import PasswordSet from '@/components/masterdata/PasswordSet.vue'

import { makeUser } from './helpers'
import { button, click, typeInto } from './dom'
import { mountView, pageText } from './layoutHelpers'

const setPassword = vi.hoisted(() => vi.fn<(id: string, password: string) => Promise<unknown>>())
vi.mock('@/api/accounts', async (importOriginal) => {
  const original = await importOriginal<typeof import('@/api/accounts')>()
  return { ...original, usersApi: { ...original.usersApi, setPassword } }
})

const row = (fields: Partial<Schemas['UserOut']> = {}) =>
  ({
    id: 'u2',
    display_name: 'Terminal',
    is_ldap_user: false,
    has_password: false,
    ...fields,
  }) as Schemas['UserOut']

const admin = makeUser({ id: 'admin', is_superuser: true, is_it_staff: true })

describe('setting the password of an employee', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => setPassword.mockReset())
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
  })

  async function drawer(fields: Partial<Schemas['UserOut']> = {}, user = admin) {
    const result = await mountView(PasswordSet, { props: { row: row(fields) }, user })
    unmount = () => result.wrapper.unmount()
  }

  it('lets an administrator set a password for a local account', async () => {
    setPassword.mockResolvedValue(row({ has_password: true }))
    await drawer()
    expect(pageText()).toContain('Password: not set')
    await click(button('Set password'))
    const fields = [
      ...document.body.querySelectorAll<HTMLInputElement>('.n-modal input[type="password"]'),
    ]
    expect(fields).toHaveLength(2)
    await typeInto(fields[0]!, 'Terminal-2026!')
    await typeInto(fields[1]!, 'Terminal-2026!')
    await click([...document.body.querySelectorAll('.n-modal button')].at(-1) as HTMLElement)
    expect(setPassword).toHaveBeenCalledWith('u2', 'Terminal-2026!')
    expect(pageText()).toContain('Password: set')
  })

  it('is hidden for directory accounts and for other IT staff', async () => {
    await drawer({ is_ldap_user: true })
    expect(pageText()).not.toContain('Password')
    unmount?.()
    document.body.innerHTML = ''
    await drawer({}, makeUser({ id: 'it', is_it_staff: true }))
    expect(pageText()).not.toContain('Password')
  })

  it('offers no button for the own account', async () => {
    await drawer({ id: 'admin', has_password: true })
    expect(pageText()).toContain('Password: set')
    expect(pageText()).not.toContain('Set password')
  })
})
