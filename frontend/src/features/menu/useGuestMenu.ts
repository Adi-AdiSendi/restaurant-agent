import { useCallback, useEffect, useRef, useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { GuestMenu } from '../../api/menuTypes'

/** The restaurant's menu as this guest sees it. `refreshKey` reloads it after a chat
 * reply, since a new allergy changes which dishes and options suit them. The caller is
 * keyed by `slug` (`MenuRoute`), so a menu never outlives its restaurant. */
export function useGuestMenu(slug: string, refreshKey: number, onUnauthorized: () => void) {
  const [menu, setMenu] = useState<GuestMenu | null>(null)
  const [error, setError] = useState<string | null>(null)
  // Only the latest request may set state, so a slow older one cannot win.
  const latest = useRef(0)

  const load = useCallback(() => {
    const request = ++latest.current
    return api.menu(slug).then(
      (loaded) => {
        if (request !== latest.current) return
        setMenu(loaded)
        setError(null)
      },
      (err: unknown) => {
        if (request !== latest.current) return
        if (err instanceof ApiError && err.status === 401) onUnauthorized()
        else setError(err instanceof ApiError ? err.message : 'Could not load the menu.')
      },
    )
  }, [slug, onUnauthorized])

  useEffect(() => {
    void load()
  }, [load, refreshKey])

  return { menu, error, reload: load }
}
