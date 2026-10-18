import { Link } from 'react-router'

import type { OrderSummary } from '../../api/cartTypes'
import DishPhoto from '../../components/DishPhoto'
import { kcalLabel } from '../../components/kcal'
import Storefront from '../../components/Storefront'
import styles from './OrderCard.module.css'
import chips from './Orders.module.css'
import { STATUS, when } from './orderLabels'

/** One past order: the restaurant's sign, the dishes, and what was paid. */
function OrderCard({ order }: { order: OrderSummary }) {
  const items = order.item_count === 1 ? '1 item' : `${order.item_count} items`
  const extra = order.item_count - order.photos.length
  return (
    <Link className={styles.card} to={`/orders/${order.id}`}>
      <div className={styles.sign}>
        <Storefront slug={order.restaurant.slug} />
      </div>
      <div className={styles.body}>
        <div className={styles.head}>
          <span className={styles.name}>{order.restaurant.name}</span>
          <span className={chips[order.status]}>{STATUS[order.status]}</span>
        </div>
        <span className={styles.meta}>
          Order {order.id} · {when(order.placed_at)} ·{' '}
          {order.fulfilment === 'pickup' ? 'Pickup' : 'Dine in'}
        </span>
        <div className={styles.dishes} aria-hidden="true">
          {order.photos.map((photo) => (
            <DishPhoto key={photo} photo={photo} icon="🍽️" size="thumb" />
          ))}
          {extra > 0 && <span className={styles.more}>+{extra}</span>}
        </div>
      </div>
      <div className={styles.paid}>
        <span className={styles.amount}>{order.total_sar} SAR</span>
        <span className={styles.meta}>{items}</span>
        {order.kcal ? <span className={styles.meta}>{kcalLabel(order.kcal)}</span> : null}
      </div>
    </Link>
  )
}

export default OrderCard
