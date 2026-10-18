import type { CartAction } from '../../api/types'
import CheckoutCard from '../orders/CheckoutCard'
import styles from './MessageBubble.module.css'

function headline({ kind, quantity, line }: CartAction): string {
  const name = line?.name ?? 'a dish'
  if (kind === 'added') return `Added ${quantity} × ${name}`
  if (kind === 'updated') return `Changed to ${quantity} × ${name}`
  if (kind === 'cleared')
    return `Emptied the cart (${quantity} ${quantity === 1 ? 'item' : 'items'})`
  return `Removed ${name}`
}

/** What the assistant changed in the cart, from the server's result, never its text. */
function ActionCard({ action }: { action: CartAction }) {
  if (action.kind === 'checkout') return <CheckoutCard />
  const line = action.line
  const details = line
    ? [...line.options.map((o) => o.name), ...line.removed.map((r) => `no ${r}`)]
    : []
  return (
    <div className={styles.action}>
      <span className={styles.actionTitle}>{headline(action)}</span>
      {details.length > 0 && <span>{details.join(', ')}</span>}
      {action.left_out.length > 0 && (
        <span className={styles.leftOut}>
          Left out {action.left_out.join(', ')}, as you prefer.
        </span>
      )}
    </div>
  )
}

export default ActionCard
