// Lives outside netlify/functions/, where every file is deployed as a function.
import { afterEach, expect, test, vi } from 'vitest'

import keepAwake, { config } from './functions/keep-awake.mts'

afterEach(() => {
  vi.unstubAllGlobals()
  vi.unstubAllEnvs()
})

test('pings the health check through the site URL every 10 minutes', async () => {
  vi.stubEnv('URL', 'https://corner-table.example')
  const fetchMock = vi.fn(() => Promise.resolve(new Response('{"status":"ok"}')))
  vi.stubGlobal('fetch', fetchMock)
  await keepAwake()
  expect(fetchMock).toHaveBeenCalledWith(
    'https://corner-table.example/api/health',
    expect.objectContaining({ signal: expect.any(AbortSignal) }),
  )
  expect(config.schedule).toBe('*/10 * * * *')
})

test('a failed ping is logged, not thrown', async () => {
  vi.stubGlobal(
    'fetch',
    vi.fn(() => Promise.reject(new Error('down'))),
  )
  await expect(keepAwake()).resolves.toBeUndefined()
})
