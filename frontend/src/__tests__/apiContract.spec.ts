import { readFileSync } from 'node:fs'
import { resolve } from 'node:path'

import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

/**
 * Every call of the API modules must hit an endpoint the backend offers, with the
 * right method: checked against the OpenAPI schema the types are generated from.
 */
const schema = JSON.parse(
  // Vitest runs in the frontend folder (see `root` in vitest.config.ts).
  readFileSync(resolve(process.cwd(), 'openapi.json'), 'utf8'),
) as { paths: Record<string, Record<string, unknown>> }

const endpoints = Object.entries(schema.paths).map(([path, operations]) => ({
  pattern: new RegExp(`^${path.replace(/\{[^}]+\}/g, '[^/]+')}$`),
  methods: Object.keys(operations).map((method) => method.toUpperCase()),
}))

function offered(method: string, url: string) {
  const path = url.split('?')[0]!
  return endpoints.some(({ pattern, methods }) => pattern.test(path) && methods.includes(method))
}

const modules = import.meta.glob<Record<string, unknown>>(
  ['@/api/*.ts', '!@/api/client.ts', '!@/api/types.ts', '!@/api/*.d.ts'],
  { eager: true },
)

type Call = (...args: unknown[]) => unknown
const calls = Object.entries(modules).flatMap(([file, exports]) =>
  Object.entries(exports).flatMap(([name, value]) =>
    value && typeof value === 'object'
      ? Object.entries(value)
          .filter((entry): entry is [string, Call] => typeof entry[1] === 'function')
          .map(([method, fn]) => [`${file.split('/').pop()} ${name}.${method}`, fn] as const)
      : [],
  ),
)

describe('API modules', () => {
  let requests: { method: string; url: string }[]

  beforeEach(() => {
    document.cookie = 'csrftoken=t; path=/'
    requests = []
    vi.stubGlobal(
      'fetch',
      vi.fn(async (url: string, init?: RequestInit) => {
        requests.push({ method: init?.method ?? 'GET', url })
        return new Response(JSON.stringify({ items: [], count: 0 }), {
          headers: { 'content-type': 'application/json' },
        })
      }),
    )
  })
  afterEach(() => vi.unstubAllGlobals())

  it('were found', () => {
    expect(calls.length).toBeGreaterThan(50)
  })

  it.each(calls)('%s calls an endpoint of the backend', async (_name, fn) => {
    await fn('0192f0c4-6a3e-7b4d-9a1e-0123456789aa', '0192f0c4-6a3e-7b4d-9a1e-0123456789ab', {})
    expect(requests.length).toBeGreaterThan(0)
    const unknown = requests.filter(({ method, url }) => !offered(method, url))
    expect(unknown).toEqual([])
  })
})
