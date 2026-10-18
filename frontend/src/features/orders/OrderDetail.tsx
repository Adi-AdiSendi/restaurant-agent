import { Link } from 'react-router'

import type { Order } from '../../api/cartTypes'
import DishPhoto from '../../components/DishPhoto'
import { kcalLabel } from '../../components/kcal'
import Storefront from '../../components/Storefront'
import styles from './OrderDetail.module.css'
import { when } from './orderLabels'
import StatusSteps from './StatusSteps'

const lineTotal = (unit: string, quantity: number) => (Number(unit) * quantity).toFixed(2)

/** One order, as a receipt: the restaurant's sign, its progress, each dish, the total. */
function OrderDetail({ order }: { order: Order }) {
  return (
    <main className={styles.page}>
      <div className={styles.sign}>
        <Storefront slug={order.restaurant.slug} />
      </div>
      <header className={styles.head}>
        <h1 className={styles.title}>Order {order.id}</h1>
        <span className={styles.meta}>
          {order.restaurant.name} · {order.fulfilment === 'pickup' ? 'Pickup' : 'Dine in'} ·{' '}
          {when(order.placed_at)}
        </span>
      </header>
      <StatusSteps status={order.status} />
      <ul className={styles.lines}>
        {order.lines.map((line, n) => (
          <li key={n} className={styles.line}>
            <DishPhoto photo={line.photo} icon="🍽️" size="thumb" />
            <div className={styles.what}>
              <span className={styles.name}>
                {line.quantity} × {line.item_name}
              </span>
              <span className={styles.meta}>
                {[...line.option_names, ...line.removed.map((r) => `no ${r}`)].join(', ')}
              </span>
              <span className={styles.meta}>
                Allergens: {line.allergens.join(', ').replaceAll('_', ' ') || 'none listed'}
              </span>
            </div>
            <div className={styles.price}>
              <span className={styles.name}>
                {lineTotal(line.unit_price_sar, line.quantity)} SAR
              </span>
              <span className={styles.meta}>{line.unit_price_sar} SAR each</span>
            </div>
          </li>
        ))}
      </ul>
      <div className={styles.total}>
        <span>Total paid at the counter</span>
        <span className={styles.amount}>{order.total_sar} SAR</span>
      </div>
      {order.kcal ? <p className={styles.meta}>{kcalLabel(order.kcal)}</p> : null}
      <Link to="/orders">All your orders</Link>
    </main>
  )
}

export default OrderDetail
