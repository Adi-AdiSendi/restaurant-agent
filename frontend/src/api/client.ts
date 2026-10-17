// The only module that calls the backend. Same origin: FastAPI serves this app
// locally, and Netlify proxies /api to the backend when deployed.
import type { AddLine, Cart, Fulfilment, Order, OrderSummary } from './cartTypes'
import type { GuestMenu, Restaurant } from './menuTypes'
import type { ChatReply, Health, LoginResponse, Me, NewConversation, Preference } from './types'

/** A cart or order error: `code` says what the UI should ask (see app/api/order_errors.py). */
export interface ErrorDetail {
  code: string
  message: string
  reasons?: string[]
  restaurant?: string
}

export class ApiError extends Error {
  readonly status: number
  readonly detail: ErrorDetail | null

  constructor(status: number, message: string, detail: ErrorDetail | null = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.detail = detail
  }
}

function structured(detail: unknown): ErrorDetail | null {
  if (typeof detail !== 'object' || detail === null || Array.isArray(detail)) return null
  return 'code' in detail && 'message' in detail ? (detail as ErrorDetail) : null
}

function detailMessage(body: unknown, fallback: string): [string, ErrorDetail | null] {
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const { detail } = body
    if (typeof detail === 'string') return [detail, null]
    if (Array.isArray(detail)) return ['Please check what you entered.', null]
    const parsed = structured(detail)
    if (parsed) return [parsed.message, parsed]
  }
  return [fallback, null]
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, {
      credentials: 'same-origin',
      headers: { 'Content-Type': 'application/json' },
      ...init,
    })
  } catch {
    throw new ApiError(0, 'Could not reach the server. Check your connection.')
  }
  if (response.status === 204) return undefined as T
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const [message, detail] = detailMessage(body, `Request failed (${response.status})`)
    throw new ApiError(response.status, message, detail)
  }
  return body as T
}

const send =
  (method: string) =>
  <T>(path: string, body?: unknown) =>
    request<T>(path, { method, body: body === undefined ? undefined : JSON.stringify(body) })
const post = send('POST')
const patch = send('PATCH')
const remove = send('DELETE')

// A waking backend holds the request until the proxy gives up (26 s); stop sooner.
const HEALTH_TIMEOUT_MS = 5_000

export const api = {
  health: () =>
    request<Health | null>('/health', { signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS) }),
  me: () => request<Me>('/auth/me'),
  login: (username: string, pin: string) => post<LoginResponse>('/auth/login', { username, pin }),
  logout: () => post<undefined>('/auth/logout'),
  restaurants: () => request<Restaurant[]>('/restaurants'),
  menu: (slug: string) => request<GuestMenu>(`/restaurants/${encodeURIComponent(slug)}/menu`),
  newConversation: (restaurant: string) => post<NewConversation>('/conversations', { restaurant }),
  sendMessage: (conversationId: number, message: string) =>
    post<ChatReply>('/chat', { conversation_id: conversationId, message }),
  getPreferences: () => request<Preference[]>('/preferences'),
  cart: () => request<Cart>('/cart'),
  addCartLine: (line: AddLine) => post<Cart>('/cart/lines', line),
  setQuantity: (lineId: number, quantity: number) =>
    patch<Cart>(`/cart/lines/${lineId}`, { quantity }),
  removeCartLine: (lineId: number) => remove<Cart>(`/cart/lines/${lineId}`),
  clearCart: () => remove<Cart>('/cart'),
  placeOrder: (fulfilment: Fulfilment, acceptedReasons: string[]) =>
    post<Order>('/orders', { fulfilment, accepted_reasons: acceptedReasons }),
  orders: () => request<OrderSummary[]>('/orders'),
  order: (orderId: number) => request<Order>(`/orders/${orderId}`),
}
