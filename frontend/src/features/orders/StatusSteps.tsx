import type { OrderStatus } from '../../api/cartTypes'
import { STATUS } from './orderLabels'
import styles from './StatusSteps.module.css'

const STEPS: OrderStatus[] = ['placed', 'preparing', 'ready']

/** Placed, preparing, ready: the steps done so far are filled in. */
function StatusSteps({ status }: { status: OrderStatus }) {
  const reached = STEPS.indexOf(status)
  return (
    <ol className={styles.steps} aria-label={`Status: ${STATUS[status]}`}>
      {STEPS.map((step, n) => (
        <li
          key={step}
          className={n <= reached ? styles.stepDone : styles.step}
          aria-current={n === reached ? 'step' : undefined}
        >
          {STATUS[step]}
        </li>
      ))}
    </ol>
  )
}

export default StatusSteps
