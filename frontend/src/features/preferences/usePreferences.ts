import { useCallback, useEffect, useMemo, useState } from 'react'

import { api, ApiError } from '../../api/client'
import type { Preference, PreferenceKind, PreferenceVocabulary } from '../../api/types'

/** What each section may do. Each resolves to whether the change was saved. */
export interface Edits {
  busy: boolean
  add: (kind: PreferenceKind, value: string) => Promise<boolean>
  change: (id: number, value: string) => Promise<boolean>
  remove: (id: number) => Promise<boolean>
}

const reason = (err: unknown, fallback: string) =>
  err instanceof ApiError ? err.message : fallback

/** The guest's preferences and the values each kind accepts, plus the edits.
 * Every edit returns the whole history from the server, so the page redraws from it. */
export function usePreferences(onUnauthorized: () => void) {
  const [prefs, setPrefs] = useState<Preference[] | null>(null)
  const [vocab, setVocab] = useState<PreferenceVocabulary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let live = true
    Promise.all([api.getPreferences(), api.preferenceVocabulary()]).then(
      ([rows, values]) => {
        if (!live) return
        setPrefs(rows)
        setVocab(values)
      },
      (err: unknown) => {
        if (err instanceof ApiError && err.status === 401) onUnauthorized()
        else if (live) setError(reason(err, 'Could not load your preferences.'))
      },
    )
    return () => {
      live = false
    }
  }, [onUnauthorized])

  const save = useCallback(
    async (change: () => Promise<Preference[]>) => {
      setBusy(true)
      setError(null)
      try {
        setPrefs(await change())
        return true
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) onUnauthorized()
        setError(reason(err, 'Could not save that change.'))
        return false
      } finally {
        setBusy(false)
      }
    },
    [onUnauthorized],
  )

  const edits: Edits = useMemo(
    () => ({
      busy,
      add: (kind, value) => save(() => api.addPreference(kind, value)),
      change: (id, value) => save(() => api.changePreference(id, value)),
      remove: (id) => save(() => api.removePreference(id)),
    }),
    [busy, save],
  )
  return { prefs, vocab, error, edits }
}

/** What each group of sections gets: the active facts, the accepted values and the edits. */
export interface SectionProps {
  active: Preference[]
  vocab: PreferenceVocabulary
  edits: Edits
}

export const ofKind = (active: Preference[], kind: PreferenceKind) =>
  active.filter((p) => p.kind === kind)
