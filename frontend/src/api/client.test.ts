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

  test('a cart error keeps its code and details for the UI', async () => {
    const detail = {
      code: 'conflict',
      message: 'Latte is not suitable: dairy.',
      reasons: ['dairy'],
    }
    mockFetch({ 'POST /api/cart/lines': { status: 409, body: { detail } } })
    const line = {
      restaurant: 'bean-and-bloom',
      item_id: 1,
      quantity: 1,
      option_ids: [],
      removed: [],
      accepted_reasons: [],
      replace_cart: false,
    }
    const error = await api.addCartLine(line).catch((e: unknown) => e)
    expect(error).toMatchObject({ status: 409, message: 'Latte is not suitable: dairy.', detail })
  })
})
