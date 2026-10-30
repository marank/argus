import { describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import { activeKey, NAVIGATION } from '@/components/layout/navigation'
import { i18n } from '@/i18n'
import { routes } from '@/router/routes'
import { RESOURCES } from '@/views/masterdata/resources'

// Resolving only; no navigation, so no page is loaded.
const router = createRouter({ history: createMemoryHistory(), routes })
const items = NAVIGATION.flatMap((section) => section.items.map((item) => ({ section, item })))
const keys = new Set(items.map(({ item }) => item.key))
const exists = (key: string) => i18n.global.te(key, 'en') && i18n.global.te(key, 'de')
const ID = '0192f0c4-6a3e-7b4d-9a1e-0123456789ab'

describe('navigation', () => {
  it('has unique entry keys', () => {
    expect(keys.size).toBe(items.length)
  })

  it('labels sections and entries in both languages', () => {
    const labels = [
      ...NAVIGATION.flatMap((section) => (section.label ? [section.label] : [])),
      ...items.map(({ item }) => item.label),
    ]
    expect(labels.filter((label) => !exists(label))).toEqual([])
  })

  it.each(items.map(({ item }) => [item.key, item] as const))(
    'links %s to an existing page',
    (_key, item) => {
      expect(router.resolve(item.to).name).not.toBe('not-found')
    },
  )

  it('hides entries the router guard would refuse', () => {
    // An entry the user sees must lead to a page the guard lets them open.
    const mismatches = items.flatMap(({ section, item }) => {
      const meta = router.resolve(item.to).meta
      const problems: string[] = []
      if (meta.module && item.module !== meta.module) problems.push('module')
      if (meta.permission && item.permission !== meta.permission) problems.push('permission')
      if (meta.approver && !item.approver) problems.push('approver')
      if (meta.superuser && !(item.superuser || section.superuser)) problems.push('superuser')
      if (meta.it && !section.it) problems.push('it')
      return problems.map((problem) => `${item.key}: ${problem}`)
    })
    expect(mismatches).toEqual([])
  })

  it('offers every master data resource', () => {
    const offered = items
      .map(({ item }) => router.resolve(item.to))
      .filter((route) => route.name === 'masterdata')
      .map((route) => route.params.resource)
    expect(offered.sort()).toEqual(Object.keys(RESOURCES).sort())
  })
})

describe('activeKey', () => {
  it.each([
    [`/inventory/assets/${ID}`, 'assets'],
    [`/inventory/licenses/${ID}`, 'licenses'],
    [`/inventory/issues/${ID}`, 'issues'],
    [`/requests/${ID}`, 'requests'],
    [`/procurement/orders/${ID}`, 'orders'],
    [`/portal/requests/${ID}`, 'portal-requests'],
    [`/portal/approvals/${ID}`, 'portal-approvals'],
    [`/portal/devices/${ID}`, 'portal-devices'],
    [`/portal/issues/${ID}`, 'portal-issues'],
    ['/settings/ldap', 'settings'],
    ['/masterdata/models', 'md-models'],
    ['/inventory/assets', 'assets'],
  ])('highlights the menu entry of %s', (path, key) => {
    const route = router.resolve(path)
    const active = activeKey(route.name as string, route.params)
    expect(active).toBe(key)
    expect(keys.has(active)).toBe(true)
  })

  it('is empty without a route name', () => {
    expect(activeKey(undefined, {})).toBe('')
  })
})
