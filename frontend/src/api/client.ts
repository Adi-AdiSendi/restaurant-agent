// The only module that calls the backend. Same origin: FastAPI serves this app
// locally, and Netlify proxies /api to the backend when deployed.
import type {
  ChatReply,
  Health,
  LoginResponse,
  Me,
  NewConversation,
  Preference,
  Restaurant,
} from './types'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function detailMessage(body: unknown, fallback: string): string {
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const { detail } = body
    if (typeof detail === 'string') return detail
    if (Array.isArray(detail)) return 'Please check what you entered.'
  }
  return fallback
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
    throw new ApiError(response.status, detailMessage(body, `Request failed (${response.status})`))
  }
  return body as T
}

const post = <T>(path: string, body?: unknown) =>
  request<T>(path, { method: 'POST', body: body === undefined ? undefined : JSON.stringify(body) })

// A waking backend holds the request until the proxy gives up (26 s); stop sooner.
const HEALTH_TIMEOUT_MS = 5_000

export const api = {
  health: () =>
    request<Health | null>('/health', { signal: AbortSignal.timeout(HEALTH_TIMEOUT_MS) }),
  me: () => request<Me>('/auth/me'),
  login: (username: string, pin: string) => post<LoginResponse>('/auth/login', { username, pin }),
  logout: () => post<undefined>('/auth/logout'),
  restaurants: () => request<Restaurant[]>('/restaurants'),
  newConversation: (restaurant: string) => post<NewConversation>('/conversations', { restaurant }),
  sendMessage: (conversationId: number, message: string) =>
    post<ChatReply>('/chat', { conversation_id: conversationId, message }),
  getPreferences: () => request<Preference[]>('/preferences'),
}
