import styles from './ConfirmBox.module.css'

interface Props {
  message: string
  action: string
  onKeep: () => void
  onConfirm: () => void
}

/** Asks before a hard rule (an allergy or the diet) is loosened or removed. */
function ConfirmBox({ message, action, onKeep, onConfirm }: Props) {
  return (
    <div className={styles.confirm} role="alertdialog" aria-label="Please confirm">
      <p>{message}</p>
      <button type="button" onClick={onKeep}>
        Keep it
      </button>{' '}
      <button className={styles.danger} type="button" onClick={onConfirm}>
        {action}
      </button>
    </div>
  )
}

export default ConfirmBox
