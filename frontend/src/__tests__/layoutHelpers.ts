import { flushPromises, mount } from '@vue/test-utils'
import { NDialogProvider, NMessageProvider } from 'naive-ui'
import { createPinia, setActivePinia } from 'pinia'
import { defineComponent, h, type Component } from 'vue'
import { createMemoryHistory, createRouter, type RouteRecordRaw } from 'vue-router'

import type { Schemas } from '@/api/types'
import ErrorPopover from '@/components/common/ErrorPopover.vue'
import { i18n } from '@/i18n'
import { routes } from '@/router/routes'
import { useAuthStore } from '@/stores/auth'
import { useFeaturesStore } from '@/stores/features'

import { makeSiteSettings, makeUser } from './helpers'

const Page = { render: () => null }

/** The app's routes with empty pages, so links resolve and navigation loads no view. */
function stubbed(records: RouteRecordRaw[]): RouteRecordRaw[] {
  return records.map(
    (record) =>
      ({
        ...record,
        ...('component' in record && record.component ? { component: Page } : {}),
        ...(record.children ? { children: stubbed(record.children) } : {}),
      }) as RouteRecordRaw,
  )
}

/** Every area readable and writable: an IT member with all roles. */
export const ALL_PERMISSIONS = Object.fromEntries(
  [
    'requests',
    'assets',
    'consumables',
    'licenses',
    'issues',
    'procurement',
    'models',
    'categories',
    'manufacturers',
    'suppliers',
    'locations',
    'departments',
    'teams',
    'users',
    'number_sequences',
  ].map((key) => [key, 'write']),
) as Schemas['CurrentUserOut']['permissions']

export interface MountOptions {
  user?: Schemas['CurrentUserOut'] | null
  /** Site flags; those not named count as on. */
  flags?: Record<string, boolean>
  site?: Partial<Schemas['SiteSettingsOut']>
  /** Leaves the site settings unloaded, for views that load them themselves. */
  siteUnloaded?: boolean
  path?: string
  props?: Record<string, unknown>
}

/**
 * Mounts a view as the app does: Naive UI's message and dialog providers, i18n,
 * Pinia with a signed-in user and the site settings, and the app's routes.
 */
export async function mountView(component: Component, options: MountOptions = {}) {
  const pinia = createPinia()
  setActivePinia(pinia)
  useAuthStore().user = options.user === undefined ? makeUser() : options.user
  if (!options.siteUnloaded)
    useFeaturesStore().settings = makeSiteSettings(options.flags ?? {}, options.site ?? {})
  const router = createRouter({ history: createMemoryHistory(), routes: stubbed(routes) })
  await router.push(options.path ?? '/')
  const wrapper = mount(
    defineComponent({
      render: () =>
        h(NMessageProvider, null, {
          default: () => [
            h(ErrorPopover),
            h(NDialogProvider, null, { default: () => h(component, options.props ?? {}) }),
          ],
        }),
    }),
    { attachTo: document.body, global: { plugins: [i18n, pinia, router] } },
  )
  await flushPromises()
  return { wrapper, router }
}

/** Visible text of the whole page, including modals and popovers teleported to the body. */
export const pageText = () => document.body.textContent ?? ''

/** The link whose text contains `text`, with its target. */
export function link(text: string): HTMLAnchorElement {
  const found = [...document.body.querySelectorAll('a')].find((a) => a.textContent?.includes(text))
  if (!found) throw new Error(`no link "${text}"`)
  return found
}
