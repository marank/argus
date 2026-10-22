import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError, http, isUnreachable } from '@/api/client'

function respond(status: number, body: string, type = 'text/plain') {
  vi.stubGlobal(
    'fetch',
    vi.fn(async () => new Response(body, { status, headers: { 'content-type': type } })),
  )
}

async function failure(): Promise<ApiError> {
  try {
    await http.get('/auth/me')
  } catch (e) {
    return e as ApiError
  }
  throw new Error('the request did not fail')
}

describe('api client', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('reports a failed connection as unreachable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => {
        throw new TypeError('Failed to fetch')
      }),
    )
    const error = await failure()
    expect(error.status).toBe(0)
    expect(isUnreachable(error)).toBe(true)
    expect(error.message).not.toContain('Failed to fetch')
  })

  it.each([502, 503, 504])(
    'reports a proxy answer %i without details as unreachable',
    async (status) => {
      respond(status, '<html>Bad Gateway</html>', 'text/html')
      const error = await failure()
      expect(isUnreachable(error)).toBe(true)
      expect(error.message).not.toContain('HTTP')
    },
  )

  it('keeps the message of other errors', async () => {
    respond(409, JSON.stringify({ detail: 'Not possible.' }), 'application/json')
    const error = await failure()
    expect(isUnreachable(error)).toBe(false)
    expect(error.message).toBe('Not possible.')
  })

  it('tells a successful delete from a failed one', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(null, { status: 204 })),
    )
    // useAction().run returns undefined for a failure; a delete must not look like one.
    expect(await http.remove('/masterdata/models/1')).toBe(true)
  })
})
