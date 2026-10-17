import { useCallback, useEffect, useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { Restaurant } from '../../api/menuTypes'

const STORAGE_KEY = 'restaurant'

// Storage can throw (private mode, blocked site data); the choice is then simply not kept.
function storedSlug(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

function storeSlug(slug: string) {
  try {
    localStorage.setItem(STORAGE_KEY, slug)
  } catch {
    // Not remembered for next time; the picker still works.
  }
}

/** The restaurants, and the one the guest is ordering from (remembered on this device). */
export function useRestaurants() {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([])
  const [slug, setSlug] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const fetchList = useCallback(
    () =>
      api.restaurants().then(
        (list) => {
          if (list.length === 0) {
            setError('No restaurants are set up yet. Please try again later.')
            return
          }
          const saved = storedSlug()
          setRestaurants(list)
          setSlug(list.some((r) => r.slug === saved) ? saved : (list[0]?.slug ?? null))
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

  const choose = useCallback((next: string) => {
    storeSlug(next)
    setSlug(next)
  }, [])

  const current = restaurants.find((r) => r.slug === slug) ?? null
  return { restaurants, current, choose, error, reload }
}
