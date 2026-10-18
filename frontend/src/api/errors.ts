// What a failed API call becomes: a status, a message to show, and for cart and order
// errors a structured detail the UI acts on.

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

/** The message to show for an error body, and its structured detail if it has one. */
export function detailMessage(body: unknown, fallback: string): [string, ErrorDetail | null] {
  if (typeof body === 'object' && body !== null && 'detail' in body) {
    const { detail } = body
    if (typeof detail === 'string') return [detail, null]
    if (Array.isArray(detail)) return ['Please check what you entered.', null]
    const parsed = structured(detail)
    if (parsed) return [parsed.message, parsed]
  }
  return [fallback, null]
}
