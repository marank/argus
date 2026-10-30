import { flushPromises } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/api/client'
import type { Schemas } from '@/api/types'
import LdapSyncView from '@/views/settings/LdapSyncView.vue'

import { makeUser } from './helpers'
import { button, click, typeInto } from './dom'
import { mountView, pageText } from './layoutHelpers'

type Item = Schemas['LdapSyncItemOut']

const api = vi.hoisted(() => ({
  get: vi.fn<() => Promise<unknown>>(),
  syncPreview: vi.fn<(query: Schemas['LdapSyncQueryIn']) => Promise<unknown>>(),
  syncApply: vi.fn<(query: Record<string, unknown>) => Promise<unknown>>(),
}))
vi.mock('@/api/settings', async (importOriginal) => ({
  ...(await importOriginal<typeof import('@/api/settings')>()),
  ldapSettingsApi: api,
}))

const settings = (fields: Partial<Schemas['LdapSettingsOut']> = {}) =>
  ({
    enabled: true,
    server_uri: 'ldaps://dc1.example.com',
    user_search_base: 'OU=Staff,DC=example,DC=com',
    user_filter: '(&(objectClass=user)(sAMAccountName={username}))',
    ...fields,
  }) as Schemas['LdapSettingsOut']

const item = (username: string, action: Item['action'], fields: Partial<Item> = {}): Item => ({
  dn: `CN=${username},OU=Staff,DC=example,DC=com`,
  username,
  action,
  changes: {},
  reason: '',
  user_id: null,
  values: { first_name: username, last_name: 'Test', email: `${username}@example.com` },
  ...fields,
})

const ITEMS: Item[] = [
  item('anna', 'create'),
  item('ben', 'update', { changes: { first_name: { old: 'Benn', new: 'Ben' } } }),
  item('carl', 'unchanged'),
  item('', 'skipped', { reason: 'no_username' }),
]

const preview = (items = ITEMS, fields: Partial<Schemas['LdapSyncPreviewOut']> = {}) => ({
  items,
  limit: 500,
  truncated: false,
  ...fields,
})

const filterField = () => document.body.querySelector<HTMLTextAreaElement>('#ldap-sync-filter')!
const baseField = () => document.body.querySelector<HTMLInputElement>('#ldap-sync-base')!
const usernames = () =>
  [...document.body.querySelectorAll('.n-data-table-tbody .n-data-table-tr')].map((row) =>
    row.querySelector('.strong')?.textContent?.trim(),
  )

describe('LDAP user sync', () => {
  let unmount: (() => void) | null = null
  beforeEach(() => {
    Object.values(api).forEach((mock) => mock.mockReset())
    api.get.mockResolvedValue(settings())
    api.syncPreview.mockResolvedValue(preview())
  })
  afterEach(() => {
    unmount?.()
    unmount = null
    document.body.innerHTML = ''
    localStorage.clear()
  })

  async function page() {
    const result = await mountView(LdapSyncView, { user: makeUser({ is_superuser: true }) })
    unmount = () => result.wrapper.unmount()
    return result
  }

  it('starts with everyone who could sign in', async () => {
    await page()
    expect(filterField().value).toBe('(&(objectClass=user)(sAMAccountName=*))')
    expect(baseField().placeholder).toBe('OU=Staff,DC=example,DC=com')
  })

  it('remembers the last query', async () => {
    localStorage.setItem('argus.ldap-sync-filter', '(department=IT)')
    await page()
    expect(filterField().value).toBe('(department=IT)')
  })

  it('fills in a template', async () => {
    await page()
    await click('Active AD accounts only')
    expect(filterField().value).toBe(
      '(&(&(objectClass=user)(sAMAccountName=*))(!(userAccountControl:1.2.840.113556.1.4.803:=2)))',
    )
  })

  it('cannot run before LDAP is enabled and saved', async () => {
    api.get.mockResolvedValue(settings({ enabled: false }))
    await page()
    expect(pageText()).toContain('Enable and save the LDAP login first.')
    expect(button('Preview').disabled).toBe(true)
  })

  describe('preview', () => {
    it('sends the trimmed query and selects what would change', async () => {
      await page()
      await typeInto(baseField(), '  OU=IT,DC=example,DC=com ')
      await click('Preview')
      expect(api.syncPreview).toHaveBeenCalledWith({
        filter: '(&(objectClass=user)(sAMAccountName=*))',
        search_base: 'OU=IT,DC=example,DC=com',
      })
      expect(pageText()).toContain('2 selected')
      expect(button('Apply (2)').disabled).toBe(false)
    })

    it.each([
      ['Ctrl', { ctrlKey: true }],
      ['Cmd', { metaKey: true }],
    ])('runs on %s+Enter in the filter', async (_, modifier) => {
      await page()
      const filter = filterField()
      filter.dispatchEvent(
        new KeyboardEvent('keydown', { key: 'Enter', bubbles: true, ...modifier }),
      )
      await flushPromises()
      expect(api.syncPreview).toHaveBeenCalledTimes(1)
    })

    it('does not run on a plain Enter in the filter', async () => {
      await page()
      const filter = filterField()
      filter.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', bubbles: true }))
      await flushPromises()
      expect(api.syncPreview).not.toHaveBeenCalled()
    })

    it('counts the entries per action and hides unchanged ones', async () => {
      await page()
      await click('Preview')
      const chips = [...document.body.querySelectorAll('.chip')].map((c) => [
        c.getAttribute('aria-pressed'),
        c.querySelector('.count')?.textContent,
      ])
      expect(chips).toEqual([
        ['true', '1'],
        ['true', '1'],
        ['false', '1'],
        ['true', '1'],
      ])
      expect(usernames()).toEqual(['anna', 'ben', '—'])
    })

    it('shows the changes and why an entry is skipped', async () => {
      await page()
      await click('Preview')
      const ben = [...document.body.querySelectorAll('.changes li')].map((li) =>
        li.textContent?.replace(/\s+/g, ' ').trim(),
      )
      expect(ben).toEqual(['First nameBennBen'])
      expect(pageText()).toContain('No username in the entry')
    })

    it('narrows the list by a search', async () => {
      await page()
      await click('Preview')
      await typeInto(
        document.body.querySelector('input[placeholder="Search results"]'),
        'BEN@example',
      )
      expect(usernames()).toEqual(['ben'])
    })

    it('warns when the directory returned more than the limit', async () => {
      api.syncPreview.mockResolvedValue(preview(ITEMS, { truncated: true, limit: 500 }))
      await page()
      await click('Preview')
      expect(pageText()).toContain('More than 500 matches')
    })

    it('shows why the search failed', async () => {
      api.syncPreview.mockRejectedValue(new ApiError(400, 'Bad search filter'))
      await page()
      await click('Preview')
      expect(pageText()).toContain('Bad search filter')
      expect(document.body.querySelector('.apply-bar')).toBeNull()
    })
  })

  describe('applying', () => {
    it('takes over the selected entries and shows what is left', async () => {
      api.syncApply.mockResolvedValue({ created: 1, updated: 1, skipped: 0 })
      await page()
      await click('Preview')
      api.syncPreview.mockResolvedValue(
        preview([item('anna', 'unchanged'), item('ben', 'unchanged')]),
      )
      await click('Apply (2)')
      expect(api.syncApply).toHaveBeenCalledWith({
        filter: '(&(objectClass=user)(sAMAccountName=*))',
        search_base: '',
        dns: [ITEMS[0]!.dn, ITEMS[1]!.dn],
      })
      expect(pageText()).toContain('1 created, 1 updated')
      expect(api.syncPreview).toHaveBeenCalledTimes(2)
      expect(pageText()).toContain('0 selected')
    })

    it('uses the query of the preview shown, not one edited since', async () => {
      api.syncApply.mockResolvedValue({ created: 1, updated: 1, skipped: 0 })
      await page()
      await click('Preview')
      await typeInto(filterField(), '(cn=other)')
      expect(pageText()).toContain('The filter or search base has changed.')
      await click('Apply (2)')
      expect(api.syncApply).toHaveBeenCalledWith(
        expect.objectContaining({ filter: '(&(objectClass=user)(sAMAccountName=*))' }),
      )
      // The editor shows the query that was applied again.
      expect(filterField().value).toBe('(&(objectClass=user)(sAMAccountName=*))')
    })

    it('takes over only the entries still selected', async () => {
      api.syncApply.mockResolvedValue({ created: 0, updated: 1, skipped: 0 })
      await page()
      await click('Preview')
      const annaRow = [
        ...document.body.querySelectorAll('.n-data-table-tbody .n-data-table-tr'),
      ][0]!
      await click(annaRow.querySelector('.n-checkbox')!)
      expect(pageText()).toContain('1 selected')
      await click('Apply (1)')
      expect(api.syncApply).toHaveBeenCalledWith(expect.objectContaining({ dns: [ITEMS[1]!.dn] }))
    })
  })
})
