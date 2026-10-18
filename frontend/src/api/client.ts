// The only module that calls the backend. Same origin: FastAPI serves this app
// locally, and Netlify proxies /api to the backend when deployed.
import type { AddLine, Cart, Fulfilment, Order, OrderSummary } from './cartTypes'
import type { GuestMenu, Restaurant } from './menuTypes'
import { ApiError, detailMessage } from './errors'
import type {
  ChatReply,
  Health,
  LoginResponse,
  Me,
  NewConversation,
  Preference,
  PreferenceKind,
  PreferenceVocabulary,
  Today,
} from './types'

export { ApiError, type ErrorDetail } from './errors'

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
  today: () => request<Today>('/preferences/today'),
  preferenceVocabulary: () => request<PreferenceVocabulary>('/preferences/vocabulary'),
  // Each edit returns the whole history, like getPreferences.
  addPreference: (kind: PreferenceKind, value: string) =>
    post<Preference[]>('/preferences', { kind, value }),
  changePreference: (id: number, value: string) =>
    patch<Preference[]>(`/preferences/${id}`, { value }),
  removePreference: (id: number) => remove<Preference[]>(`/preferences/${id}`),
  cart: () => request<Cart>('/cart'),
  addCartLine: (line: AddLine) => post<Cart>('/cart/lines', line),
  setQuantity: (lineId: number, quantity: number) =>
    patch<Cart>(`/cart/lines/${lineId}`, { quantity }),
  removeCartLine: (lineId: number) => remove<Cart>(`/cart/lines/${lineId}`),
  clearCart: () => remove<Cart>('/cart'),
  /** `expectedTotal`: the total the guest saw; the server refuses a cart that changed since. */
  placeOrder: (fulfilment: Fulfilment, acceptedReasons: string[], expectedTotal: string) => {
    const body = {
      fulfilment,
      accepted_reasons: acceptedReasons,
      expected_total_sar: expectedTotal,
    }
    return post<Order>('/orders', body)
  },
  orders: () => request<OrderSummary[]>('/orders'),
  order: (orderId: number) => request<Order>(`/orders/${orderId}`),
}
