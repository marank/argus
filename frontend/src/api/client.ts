/**
 * Thin fetch wrapper for the Django API.
 *
 * Authentication uses the Django session cookie; unsafe requests send the
 * `csrftoken` cookie back as `X-CSRFToken` header.
 */

import { i18n } from '@/i18n'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly errors: Record<string, string[]> = {},
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

/**
 * No connection (status 0), or the proxy in front found no backend: nginx or the
 * Vite dev server answer 502/504, the health check 503 while the database is down.
 */
const UNREACHABLE_STATUSES = new Set([0, 502, 503, 504])

export function isUnreachable(error: unknown): boolean {
  return error instanceof ApiError && UNREACHABLE_STATUSES.has(error.status)
}

function unreachable(): ApiError {
  return new ApiError(0, i18n.global.t('common.unreachable'))
}

/** ``fetch``, with a failed connection reported as an ApiError (status 0). */
async function send(url: string, init: RequestInit): Promise<Response> {
  try {
    return await fetch(url, init)
  } catch {
    throw unreachable()
  }
}

type Query = Record<string, string | number | boolean | null | undefined | (string | number)[]>

const BASE_URL = '/api'
const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])

let unauthorizedHandler: (() => void) | null = null

export function onUnauthorized(handler: () => void) {
  unauthorizedHandler = handler
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(new RegExp(`(?:^|; )${name}=([^;]*)`))
  return match ? decodeURIComponent(match[1]!) : null
}

export async function ensureCsrfCookie(): Promise<void> {
  if (!readCookie('csrftoken')) {
    await send(`${BASE_URL}/auth/csrf`, { credentials: 'same-origin', cache: 'no-store' })
  }
}

function buildUrl(path: string, query?: Query): string {
  const url = new URL(`${BASE_URL}${path}`, window.location.origin)
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null || value === '') continue
    if (Array.isArray(value)) value.forEach((v) => url.searchParams.append(key, String(v)))
    else url.searchParams.set(key, String(value))
  }
  return url.pathname + url.search
}

function errorMessage(body: unknown, status: number): string {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail: unknown }).detail
    if (typeof detail === 'string') return detail
    // Pydantic validation errors: [{loc: [...], msg: '...'}]
    if (Array.isArray(detail)) {
      return detail
        .map((d: { loc?: unknown[]; msg?: string }) => {
          const field = d.loc?.filter((p) => typeof p === 'string' && p !== 'body').join('.')
          return field ? `${field}: ${d.msg}` : d.msg
        })
        .join('; ')
    }
  }
  if (UNREACHABLE_STATUSES.has(status)) return i18n.global.t('common.unreachable')
  return `HTTP ${status}`
}

export async function request<T>(
  method: string,
  path: string,
  options: { query?: Query; body?: unknown } = {},
): Promise<T> {
  const headers: Record<string, string> = {
    Accept: 'application/json',
    // Backend messages (validation, business rules) follow the UI language.
    'Accept-Language': document.documentElement.lang || 'en',
  }
  if (!SAFE_METHODS.has(method)) {
    await ensureCsrfCookie()
    headers['X-CSRFToken'] = readCookie('csrftoken') ?? ''
  }
  if (options.body !== undefined) headers['Content-Type'] = 'application/json'

  const response = await send(buildUrl(path, options.query), {
    method,
    headers,
    credentials: 'same-origin',
    cache: 'no-store',
    body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
  })

  if (response.status === 204) return undefined as T
  const body = response.headers.get('content-type')?.includes('json') ? await response.json() : null

  if (!response.ok) {
    if (response.status === 401 && unauthorizedHandler && !path.startsWith('/auth/')) {
      unauthorizedHandler()
    }
    throw new ApiError(response.status, errorMessage(body, response.status), body?.errors ?? {})
  }
  return body as T
}

export const http = {
  get: <T>(path: string, query?: Query) => request<T>('GET', path, { query }),
  post: <T>(path: string, body?: unknown) => request<T>('POST', path, { body: body ?? {} }),
  put: <T>(path: string, body: unknown) => request<T>('PUT', path, { body }),
  patch: <T>(path: string, body: unknown) => request<T>('PATCH', path, { body }),
  delete: <T = void>(path: string) => request<T>('DELETE', path),
}

export type { Query }
