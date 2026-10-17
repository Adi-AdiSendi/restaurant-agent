import { useCallback, useEffect, useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { Restaurant } from '../../api/menuTypes'

/** Every restaurant in the app, in display order. */
export function useRestaurants() {
  const [restaurants, setRestaurants] = useState<Restaurant[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchList = useCallback(
    () =>
      api.restaurants().then(
        (list) => {
          if (list.length === 0) setError('No restaurants are set up yet. Please try again later.')
          else setRestaurants(list)
        },
        (err: unknown) =>
          setError(err instanceof ApiError ? err.message : 'Could not load the restaurants.'),
      ),
    [],
  )

  useEffect(() => {
    void fetchList()
  }, [fetchList])

  const reload = useCallback(() => {
    setError(null)
    void fetchList()
  }, [fetchList])

  return { restaurants, error, reload }
}
