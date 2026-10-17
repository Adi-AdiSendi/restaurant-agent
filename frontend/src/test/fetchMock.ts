import { vi } from 'vitest'

type Route = { status?: number; body?: unknown }

/** Replace fetch with canned responses keyed by "METHOD /path". A list of
 * responses is served in order, and the last one repeats. */
export function mockFetch(routes: Record<string, Route | Route[]>) {
  const fetchMock = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const key = `${init?.method ?? 'GET'} ${String(input)}`
    const entry = routes[key]
    const route = Array.isArray(entry) ? (entry.length > 1 ? entry.shift() : entry[0]) : entry
    if (!route) return Promise.reject(new Error(`Unexpected request: ${key}`))
    const status = route.status ?? 200
    const body = status === 204 ? null : JSON.stringify(route.body ?? {})
    return Promise.resolve(new Response(body, { status }))
  })
  vi.stubGlobal('fetch', fetchMock)
  return fetchMock
}
