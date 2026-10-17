// @vitest-environment node
// Lives outside netlify/functions/, where every file is deployed as a function.
import { readFileSync } from 'node:fs'

import { afterEach, expect, test, vi } from 'vitest'

import keepAwake, { BACKEND_HEALTH_URL, config } from './functions/keep-awake.mts'

afterEach(() => {
  vi.unstubAllGlobals()
})

test('pings the backend health check directly every 10 minutes', async () => {
  const fetchMock = vi.fn(() => Promise.resolve(new Response('{"status":"ok"}')))
  vi.stubGlobal('fetch', fetchMock)
  await keepAwake()
  expect(fetchMock).toHaveBeenCalledWith(
    BACKEND_HEALTH_URL,
    expect.objectContaining({ signal: expect.any(AbortSignal) }),
  )
  expect(config.schedule).toBe('@yearly')
})

test('pings the same backend that netlify.toml proxies /api to', () => {
  const toml = readFileSync(new URL('../../netlify.toml', import.meta.url), 'utf8')
  const proxied = /to = "(https:\/\/[^"]+)\/api\/:splat"/.exec(toml)?.[1]
  expect(`${proxied ?? 'missing'}/api/health`).toBe(BACKEND_HEALTH_URL)
})

test('a failed ping is logged, not thrown', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.reject(new Error('down'))),
  )
  await expect(keepAwake()).resolves.toBeUndefined()
})
