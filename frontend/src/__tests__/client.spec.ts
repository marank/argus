import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { ApiError, ensureCsrfCookie, http, isUnreachable, onUnauthorized } from '@/api/client'

type Fetch = (url: string, init?: RequestInit) => Promise<Response>
type FetchMock = ReturnType<typeof vi.fn<Fetch>>

function respond(status: number, body: string, type = 'text/plain'): FetchMock {
  const fetch = vi.fn<Fetch>(
    async () => new Response(body, { status, headers: { 'content-type': type } }),
  )
  vi.stubGlobal('fetch', fetch)
  return fetch
}

const json = (status: number, body: unknown) =>
  respond(status, JSON.stringify(body), 'application/json')

async function failure(call: () => Promise<unknown> = () => http.get('/auth/me')) {
  try {
    await call()
  } catch (e) {
    return e as ApiError
  }
  throw new Error('the request did not fail')
}

function setCookie(value: string) {
  document.cookie = `csrftoken=${value}; path=/`
}

function clearCookie() {
  document.cookie = 'csrftoken=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
}

const headersOf = (fetch: FetchMock, call = 0) =>
  fetch.mock.calls[call]![1]!.headers as Record<string, string>

describe('api client', () => {
  beforeEach(clearCookie)
  afterEach(() => {
    vi.unstubAllGlobals()
    clearCookie()
  })

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
    json(409, { detail: 'Not possible.' })
    const error = await failure()
    expect(isUnreachable(error)).toBe(false)
    expect(error.message).toBe('Not possible.')
  })

  it('does not count other errors or plain exceptions as unreachable', () => {
    expect(isUnreachable(new ApiError(500, 'boom'))).toBe(false)
    expect(isUnreachable(new Error('boom'))).toBe(false)
    expect(isUnreachable(null)).toBe(false)
  })

  it('tells a successful delete from a failed one', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(null, { status: 204 })),
    )
    // useAction().run returns undefined for a failure; a delete must not look like one.
    expect(await http.remove('/masterdata/models/1')).toBe(true)
  })

  it('answers undefined for 204 No Content', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => new Response(null, { status: 204 })),
    )
    expect(await http.delete('/masterdata/models/1')).toBeUndefined()
  })

  it('returns the parsed JSON body', async () => {
    json(200, { id: 'a1' })
    expect(await http.get('/things/a1')).toEqual({ id: 'a1' })
  })

  it('returns null for a successful answer that is not JSON', async () => {
    respond(200, 'ok')
    expect(await http.get('/health')).toBeNull()
  })

  describe('urls', () => {
    it('prefixes the API base path', async () => {
      const fetch = json(200, {})
      await http.get('/things')
      expect(fetch.mock.calls[0]![0]).toBe('/api/things')
    })

    it('leaves out empty query values and repeats arrays', async () => {
      const fetch = json(200, {})
      await http.get('/things', {
        q: 'laptop',
        page: 2,
        mine: false,
        empty: '',
        none: null,
        missing: undefined,
        status: ['open', 'in_progress'],
      })
      const url = new URL(fetch.mock.calls[0]![0], 'http://x')
      expect(url.pathname).toBe('/api/things')
      expect([...url.searchParams]).toEqual([
        ['q', 'laptop'],
        ['page', '2'],
        ['mine', 'false'],
        ['status', 'open'],
        ['status', 'in_progress'],
      ])
    })

    it('encodes special characters in query values', async () => {
      const fetch = json(200, {})
      await http.get('/things', { q: 'a&b c' })
      expect(new URL(fetch.mock.calls[0]![0], 'http://x').searchParams.get('q')).toBe('a&b c')
    })
  })

  describe('headers and body', () => {
    it('sends no CSRF token and no body on reads', async () => {
      const fetch = json(200, {})
      await http.get('/things')
      const init = fetch.mock.calls[0]![1]!
      expect(init.method).toBe('GET')
      expect(init.body).toBeUndefined()
      expect(init.credentials).toBe('same-origin')
      expect(headersOf(fetch)).not.toHaveProperty('X-CSRFToken')
      expect(headersOf(fetch)).not.toHaveProperty('Content-Type')
      expect(headersOf(fetch).Accept).toBe('application/json')
    })

    it('asks for messages in the page language', async () => {
      document.documentElement.lang = 'de'
      const fetch = json(200, {})
      await http.get('/things')
      expect(headersOf(fetch)['Accept-Language']).toBe('de')
      document.documentElement.lang = 'en'
    })

    it('sends the CSRF cookie back as header on changes', async () => {
      setCookie('tok%2Fen')
      const fetch = json(200, {})
      await http.patch('/things/1', { name: 'x' })
      // The cookie was there, so it was not fetched first.
      expect(fetch).toHaveBeenCalledOnce()
      expect(headersOf(fetch)['X-CSRFToken']).toBe('tok/en')
      expect(headersOf(fetch)['Content-Type']).toBe('application/json')
      expect(fetch.mock.calls[0]![1]!.body).toBe('{"name":"x"}')
    })

    it('fetches the CSRF cookie first when it is missing', async () => {
      const fetch = vi.fn<Fetch>(async (url) => {
        if (url === '/api/auth/csrf') setCookie('fresh')
        return new Response('{}', { headers: { 'content-type': 'application/json' } })
      })
      vi.stubGlobal('fetch', fetch)
      await http.put('/things/1', { name: 'x' })
      expect(fetch.mock.calls.map(([url]) => url)).toEqual(['/api/auth/csrf', '/api/things/1'])
      expect(headersOf(fetch, 1)['X-CSRFToken']).toBe('fresh')
    })

    it('sends an empty token when the cookie cannot be had', async () => {
      const fetch = json(200, {})
      await http.delete('/things/1')
      expect(headersOf(fetch, 1)['X-CSRFToken']).toBe('')
    })

    it('posts an empty object when there is no body', async () => {
      setCookie('t')
      const fetch = json(200, {})
      await http.post('/things/1/archive')
      expect(fetch.mock.calls[0]![1]!.body).toBe('{}')
      expect(fetch.mock.calls[0]![1]!.method).toBe('POST')
    })

    it('ensureCsrfCookie does nothing when the cookie is set', async () => {
      setCookie('t')
      const fetch = json(200, {})
      await ensureCsrfCookie()
      expect(fetch).not.toHaveBeenCalled()
    })
  })

  describe('error messages', () => {
    it('lists validation errors with their field', async () => {
      json(422, {
        detail: [
          { loc: ['body', 'payload', 'name'], msg: 'Field required' },
          { loc: ['body'], msg: 'Invalid body' },
          { msg: 'Something else' },
        ],
      })
      const error = await failure()
      expect(error.status).toBe(422)
      expect(error.message).toBe('payload.name: Field required; Invalid body; Something else')
    })

    it('keeps the field errors of the body', async () => {
      json(400, { detail: 'Please check the form.', errors: { name: ['Taken.'] } })
      const error = await failure()
      expect(error.errors).toEqual({ name: ['Taken.'] })
    })

    it('has no field errors when the body has none', async () => {
      respond(500, 'oops')
      const error = await failure()
      expect(error.errors).toEqual({})
    })

    it('falls back to the status for an answer without details', async () => {
      respond(500, 'Internal Server Error')
      const error = await failure()
      expect(error.message).toBe('HTTP 500')
      expect(error.name).toBe('ApiError')
      expect(error).toBeInstanceOf(Error)
    })

    it('falls back to the status for JSON without a detail', async () => {
      json(418, { message: 'teapot' })
      expect((await failure()).message).toBe('HTTP 418')
    })

    it('prefers a detail of the backend over the unreachable message', async () => {
      json(503, { detail: 'Maintenance until 10:00.' })
      const error = await failure()
      expect(error.message).toBe('Maintenance until 10:00.')
      expect(isUnreachable(error)).toBe(true)
    })
  })

  describe('unauthorized handler', () => {
    const handler = vi.fn<() => void>()
    beforeEach(() => {
      handler.mockReset()
      onUnauthorized(handler)
    })

    it('is called on a 401 of an ordinary request', async () => {
      json(401, { detail: 'Not logged in.' })
      const error = await failure(() => http.get('/things'))
      expect(error.status).toBe(401)
      expect(handler).toHaveBeenCalledOnce()
    })

    it('is not called for the auth endpoints, which answer 401 for wrong credentials', async () => {
      json(401, { detail: 'Wrong password.' })
      await failure(() => http.get('/auth/me'))
      expect(handler).not.toHaveBeenCalled()
    })

    it('is not called for other errors', async () => {
      json(403, { detail: 'Forbidden.' })
      await failure(() => http.get('/things'))
      expect(handler).not.toHaveBeenCalled()
    })
  })
})
