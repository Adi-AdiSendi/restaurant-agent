import PastFacts from '../memory/PastFacts'
import FoodTastes from './FoodTastes'
import HardRules from './HardRules'
import styles from './Preferences.module.css'
import SoftLimits from './SoftLimits'
import { usePreferences } from './usePreferences'

/** Everything the assistant remembers, edited by hand. The chat and this page
 * change the same profile through the same rules (ADR 0026). */
function PreferencesPage({ onUnauthorized }: { onUnauthorized: () => void }) {
  const { prefs, vocab, error, edits } = usePreferences(onUnauthorized)
  const active = prefs?.filter((p) => p.status === 'active') ?? []

  return (
    <main className={styles.page}>
      <h1 className={styles.title}>Your preferences</h1>
      <p className={styles.note}>
        What the assistant remembers about you. Change it here, or just tell the chat: both update
        the same profile.
      </p>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      {prefs && vocab ? (
        <>
          <HardRules active={active} vocab={vocab} edits={edits} />
          <SoftLimits active={active} vocab={vocab} edits={edits} />
          <FoodTastes active={active} vocab={vocab} edits={edits} />
          <PastFacts rows={prefs.filter((p) => p.status !== 'active').slice(0, 10)} />
        </>
      ) : (
        !error && <p className={styles.note}>Loading your preferences…</p>
      )}
    </main>
  )
}

export default PreferencesPage
