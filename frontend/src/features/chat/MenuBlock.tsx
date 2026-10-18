import type { Card } from '../../api/menuTypes'
import type { MenuBlock as Block } from '../../api/types'
import { categoryIcon } from '../../components/categoryIcon'
import DishPhoto from '../../components/DishPhoto'
import styles from './MenuBlock.module.css'
import { addLabel, canQuickAdd, type QuickAdd } from './quickAdd'

const title = (category: string) => {
  const words = category.replaceAll('_', ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

interface Props {
  block: Block
  onChoose?: (item: Card) => void
  quickAdd?: QuickAdd
}

/** A category the guest asked to see, from the server's tool result. Showing is not
 * recommending: dishes that do not suit the guest say why, and cannot be added here. */
function MenuBlock({ block, onChoose, quickAdd }: Props) {
  return (
    <section className={styles.block} aria-label={`Menu: ${title(block.category)}`}>
      <h3 className={styles.title}>{title(block.category)}</h3>
      <ul className={styles.rows}>
        {block.items.map((item) => {
          const unsuitable = item.conflicts_with_guest.length > 0
          const from = item.option_groups.length > 0 ? 'from ' : ''
          return (
            <li key={item.id} className={unsuitable ? styles.rowOff : styles.row}>
              <DishPhoto photo={item.photo} icon={categoryIcon(item.category)} size="thumb" />
              <span className={styles.name}>{item.name}</span>
              <span className={styles.price}>
                {from}
                {item.price_sar} SAR
              </span>
              {item.may_contain_warnings.length > 0 && (
                <span className={styles.trace}>
                  may contain {item.may_contain_warnings.join(', ').replaceAll('_', ' ')}
                </span>
              )}
              {unsuitable ? (
                <span className={styles.reason}>
                  not for you: {item.conflicts_with_guest.join(', ')}
                </span>
              ) : quickAdd && canQuickAdd(item) ? (
                <button
                  className={styles.add}
                  type="button"
                  aria-label={addLabel(item, quickAdd)}
                  disabled={quickAdd.pending !== null}
                  onClick={() => quickAdd.add(item)}
                >
                  {quickAdd.added === item.id ? 'Added ✓' : 'Add'}
                </button>
              ) : (
                onChoose && (
                  <button
                    className={styles.add}
                    type="button"
                    aria-label={`Choose options for ${item.name}`}
                    onClick={() => onChoose(item)}
                  >
                    Options
                  </button>
                )
              )}
            </li>
          )
        })}
      </ul>
    </section>
  )
}

export default MenuBlock
