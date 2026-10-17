import styles from './StartupScreen.module.css'

interface Props {
  down: boolean
  onRetry: () => void
}

function StartupScreen({ down, onRetry }: Props) {
  return (
    <main className={styles.page}>
      <section className={styles.card} aria-live="polite">
        <img className={styles.logo} src="/foodics-logo.svg" alt="Foodics" />
        <h1 className={styles.title}>Corner Table</h1>
        {down ? (
          <>
            <p className={styles.error} role="alert">
              The server did not start. Please try again in a minute.
            </p>
            <button className={styles.button} type="button" onClick={onRetry}>
              Try again
            </button>
          </>
        ) : (
          <>
            <p className={styles.status}>Starting the server…</p>
            <p className={styles.hint}>
              The server goes to sleep when nobody has used the demo for a while. Waking it can take
              up to a minute.
            </p>
          </>
        )}
      </section>
    </main>
  )
}

export default StartupScreen
