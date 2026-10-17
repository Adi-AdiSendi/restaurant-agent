import styles from './AddConfirm.module.css'
import type { Ask } from './useAddLine'

interface Props {
  ask: Ask
  busy: boolean
  onYes: () => void
  onNo: () => void
}

/** The guest's own decision, asked plainly. The assistant can never answer this for them. */
function AddConfirm({ ask, busy, onYes, onNo }: Props) {
  const conflict = ask.kind === 'conflict'
  return (
    <div
      className={conflict ? styles.confirmDanger : styles.confirm}
      role="alertdialog"
      aria-label="Please confirm"
    >
      <p className={styles.confirmText}>
        {conflict
          ? `${ask.message} It breaks your saved allergies or diet. Add it anyway?`
          : `Your cart has dishes from ${ask.restaurant}. Empty it and start a new cart here?`}
      </p>
      <div className={styles.confirmActions}>
        <button className={styles.secondary} type="button" onClick={onNo} disabled={busy}>
          {conflict ? 'No, keep it out' : 'Keep my cart'}
        </button>
        <button className={styles.danger} type="button" onClick={onYes} disabled={busy}>
          {conflict ? 'Add anyway' : 'Start a new cart'}
        </button>
      </div>
    </div>
  )
}

export default AddConfirm
