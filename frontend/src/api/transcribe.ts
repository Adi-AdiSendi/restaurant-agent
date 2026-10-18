// Voice to text on the server, for browsers without speech recognition.
import { ApiError, detailMessage } from './errors'

/** Posts the recorded clip as-is and returns what was said. */
export async function transcribe(audio: Blob): Promise<string> {
  let response: Response
  try {
    response = await fetch('/api/transcribe', {
      method: 'POST',
      credentials: 'same-origin',
      headers: { 'Content-Type': audio.type || 'audio/webm' },
      body: audio,
    })
  } catch {
    throw new ApiError(0, 'Could not reach the server. Check your connection.')
  }
  const body: unknown = await response.json().catch(() => null)
  if (!response.ok) {
    const [message, detail] = detailMessage(body, 'Could not understand the recording.')
    throw new ApiError(response.status, message, detail)
  }
  return (body as { text: string }).text
}
