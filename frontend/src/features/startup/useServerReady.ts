import { useCallback, useEffect, useState } from 'react'

import { api } from '../../api/client'

// The free backend sleeps when idle and takes about a minute to wake up.
export const RETRY_MS = 3_000
export const GIVE_UP_MS = 120_000
// A normal load answers well within this, so the startup screen does not flash.
export const SLOW_MS = 1_000

export type ServerState = 'checking' | 'waking' | 'ready' | 'down'

async function isUp(): Promise<boolean> {
  try {
    // A wake-up page or a proxy timeout is not JSON with status "ok".
    return (await api.health())?.status === 'ok'
  } catch {
    return false
  }
}

/** Polls /api/health until the backend answers, then reports 'ready'. */
export function useServerReady() {
  const [state, setState] = useState<ServerState>('checking')
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    let timer: ReturnType<typeof setTimeout> | undefined
    const started = Date.now()
    const slow = setTimeout(() => setState((s) => (s === 'checking' ? 'waking' : s)), SLOW_MS)

    async function check() {
      const up = await isUp()
      if (cancelled) return
      clearTimeout(slow)
      if (up) {
        setState('ready')
      } else if (Date.now() - started >= GIVE_UP_MS) {
        setState('down')
      } else {
        setState('waking')
        timer = setTimeout(() => void check(), RETRY_MS)
      }
    }

    void check()
    return () => {
      cancelled = true
      clearTimeout(timer)
      clearTimeout(slow)
    }
  }, [attempt])

  const retry = useCallback(() => {
    setState('waking')
    setAttempt((n) => n + 1)
  }, [])

  return { state, retry }
}
