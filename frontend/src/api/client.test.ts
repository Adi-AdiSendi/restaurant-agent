import { describe, expect, test } from 'vitest'

import { mockFetch } from '../test/fetchMock'
import { api, ApiError } from './client'

describe('api client', () => {
  test('returns the parsed body on success', async () => {
    mockFetch({ 'GET /api/auth/me': { body: { username: 'sara' } } })
    await expect(api.me()).resolves.toEqual({ username: 'sara' })
  })

  test('turns an error status into ApiError with the server detail', async () => {
    mockFetch({
      'POST /api/chat': { status: 503, body: { detail: 'The assistant is unavailable.' } },
    })
    const error = await api.sendMessage(1, 'hi').catch((e: unknown) => e)
    expect(error).toBeInstanceOf(ApiError)
    expect(error).toMatchObject({ status: 503, message: 'The assistant is unavailable.' })
  })

  test('validation errors get a readable message', async () => {
    mockFetch({ 'POST /api/auth/login': { status: 422, body: { detail: [{ msg: 'bad' }] } } })
    await expect(api.login('x', '1')).rejects.toMatchObject({
      status: 422,
      message: 'Please check what you entered.',
    })
  })

  test('a 204 resolves without a body', async () => {
    mockFetch({ 'POST /api/auth/logout': { status: 204 } })
    await expect(api.logout()).resolves.toBeUndefined()
  })
})
