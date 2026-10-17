// The only module that calls the backend. Same origin: FastAPI serves this app.
import type { ChatReply, LoginResponse, Me, NewConversation, Preference } from './types'

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

export const api = {
  me: () => request<Me>('/auth/me'),
  login: (username: string, pin: string) => post<LoginResponse>('/auth/login', { username, pin }),
  logout: () => post<undefined>('/auth/logout'),
  newConversation: () => post<NewConversation>('/conversations'),
  sendMessage: (conversationId: number, message: string) =>
    post<ChatReply>('/chat', { conversation_id: conversationId, message }),
  getPreferences: () => request<Preference[]>('/preferences'),
}
