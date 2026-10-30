import { describe, expect, it } from 'vitest'
import {
  createMemoryHistory,
  createRouter,
  type RouteLocationNormalized,
  type RouteRecordRaw,
} from 'vue-router'

import { i18n } from '@/i18n'
import { routes } from '@/router/routes'

const ID = '0192f0c4-6a3e-7b4d-9a1e-0123456789ab'

// Resolving only; no navigation, so no page is loaded.
const router = createRouter({ history: createMemoryHistory(), routes })

function flatten(records: RouteRecordRaw[]): RouteRecordRaw[] {
  return records.flatMap((record) => [record, ...flatten(record.children ?? [])])
}

const all = flatten(routes)
const exists = (key: string) => i18n.global.te(key, 'en') && i18n.global.te(key, 'de')

/** The props the page component gets for `path`. */
function propsOf(path: string) {
  const route = router.resolve(path)
  const props = route.matched.at(-1)!.props.default
  return typeof props === 'function' ? props(route as RouteLocationNormalized) : props
}

describe('routes', () => {
  it('have unique names', () => {
    const names = all.map((record) => record.name).filter(Boolean)
    expect(new Set(names).size).toBe(names.length)
  })

  it('give every named page a title in both languages', () => {
    const pages = all.filter((record) => record.name && 'component' in record && record.component)
    const untitled = pages
      .filter((record) => record.name !== 'not-found' && record.path !== '/')
      .filter((record) => !record.meta?.title || !exists(record.meta.title))
      .map((record) => String(record.name))
    expect(untitled).toEqual([])
  })

  it.each([
    ['/requests/ID', 'request'],
    ['/inventory/assets/ID', 'asset'],
    ['/inventory/licenses/ID', 'license'],
    ['/procurement/orders/ID', 'order'],
    ['/portal/requests/ID', 'portal-request'],
    ['/terminal/ID', 'terminal-pickup'],
    ['/requests/ID/protocol', 'handover-protocol'],
  ])('passes the id of %s to the page', (path, name) => {
    const url = path.replace('ID', ID)
    expect(router.resolve(url).name).toBe(name)
    expect(propsOf(url)).toEqual({ id: ID })
  })

  it('tells the issue page who is looking', () => {
    expect(propsOf(`/inventory/issues/${ID}`)).toEqual({ id: ID, viewer: 'it' })
    expect(propsOf(`/portal/issues/${ID}`)).toEqual({ id: ID, viewer: 'reporter' })
  })

  it('does not take anything but a UUID as id', () => {
    expect(router.resolve('/requests/123').name).toBe('not-found')
    expect(router.resolve('/inventory/assets/new').name).toBe('not-found')
  })

  it('shows unknown paths as not found', () => {
    expect(router.resolve('/no/such/page').name).toBe('not-found')
  })

  it('restricts settings to administrators, including their sub-pages', () => {
    expect(router.resolve('/settings/ldap/sync').meta).toMatchObject({
      superuser: true,
      section: 'settings-ldap',
    })
    expect(router.resolve('/settings/mail').meta.superuser).toBe(true)
  })

  it('restricts IT pages to IT staff with the right of the area', () => {
    expect(router.resolve('/inventory/assets').meta).toMatchObject({
      it: true,
      permission: 'assets',
    })
    expect(router.resolve('/procurement/orders').meta).toMatchObject({
      it: true,
      module: 'procurement',
    })
  })

  it('keeps the filters of the old stock link', () => {
    const record = all.find((r) => r.path === 'inventory/stock')!
    const redirect = record.redirect as (to: RouteLocationNormalized) => unknown
    const to = router.resolve('/inventory/stock?low=1')
    expect(redirect(to as RouteLocationNormalized)).toEqual({
      name: 'consumables',
      query: { low: '1' },
    })
  })

  it('opens the first settings section by default', () => {
    expect(all.find((r) => r.name === 'settings')!.redirect).toEqual({
      name: 'settings-features',
    })
  })

  it('names the master data resource in the path', () => {
    expect(router.resolve('/masterdata/models').params).toEqual({ resource: 'models' })
    expect(propsOf('/masterdata/models')).toBe(true)
  })
})
