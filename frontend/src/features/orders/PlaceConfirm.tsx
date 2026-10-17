import styles from './Orders.module.css'

interface Props {
  message: string
  busy: boolean
  onBack: () => void
  onPlace: () => void
}

/** The guest's own decision to order despite a conflict with their saved profile. */
function PlaceConfirm({ message, busy, onBack, onPlace }: Props) {
  return (
    <div className={styles.confirm} role="alertdialog" aria-label="Please confirm">
      <p>{message} Place the order anyway?</p>
      <button type="button" onClick={onBack}>
        Go back
      </button>{' '}
      <button className={styles.danger} type="button" disabled={busy} onClick={onPlace}>
        Place it anyway
      </button>
    </div>
  )
}

export default PlaceConfirm
