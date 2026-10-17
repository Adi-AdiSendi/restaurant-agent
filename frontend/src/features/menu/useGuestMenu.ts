import { useCallback, useEffect, useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { GuestMenu } from '../../api/menuTypes'

/** The restaurant's menu as this guest sees it. `refreshKey` reloads it after a chat
 * reply, since a new allergy changes which dishes and options suit them. */
export function useGuestMenu(slug: string, refreshKey: number, onUnauthorized: () => void) {
  const [menu, setMenu] = useState<GuestMenu | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(
    () =>
      api.menu(slug).then(
        (loaded) => {
          setMenu(loaded)
          setError(null)
        },
        (err: unknown) => {
          if (err instanceof ApiError && err.status === 401) onUnauthorized()
          else setError(err instanceof ApiError ? err.message : 'Could not load the menu.')
        },
      ),
    [slug, onUnauthorized],
  )

  useEffect(() => {
    void load()
  }, [load, refreshKey])

  return { menu: menu?.restaurant.slug === slug ? menu : null, error, reload: load }
}
