import styles from './Skeleton.module.css'

interface Props {
  /** How many placeholder cards. */
  count: number
  label: string
}

/** Grey placeholder cards while a list loads, so the page does not jump when it arrives. */
function Skeleton({ count, label }: Props) {
  return (
    <div className={styles.grid} role="status" aria-label={label}>
      {Array.from({ length: count }, (_, n) => (
        <div key={n} className={styles.card}>
          <div className={styles.photo} />
          <div className={styles.line} />
          <div className={styles.lineShort} />
        </div>
      ))}
    </div>
  )
}

export default Skeleton
