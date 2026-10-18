import type { Allergen, Card } from '../../api/menuTypes'
import { categoryIcon } from '../../components/categoryIcon'
import DishPhoto from '../../components/DishPhoto'
import ItemBadges from './ItemBadges'
import styles from './ItemCard.module.css'
import ItemOptions from './ItemOptions'
import { addLabel, canQuickAdd, type QuickAdd } from './quickAdd'

const allergenLabel = (allergen: Allergen) => allergen.replace('_', ' ')

interface Props {
  item: Card
  /** Opens the options sheet, so the guest can add it to the cart. */
  onChoose?: () => void
  /** Adds it in one click, when no choice is needed and nothing conflicts. */
  quickAdd?: QuickAdd
}

// Every detail comes from the card data the backend loaded from the database,
// never from the assistant's text. Allergens are always visible.
function ItemCard({ item, onChoose, quickAdd }: Props) {
  const traces = item.may_contain.filter((a) => !item.may_contain_warnings.includes(a))
  return (
    <article className={styles.card} aria-label={item.name}>
      <DishPhoto photo={item.photo} icon={categoryIcon(item.category)} />
      <header className={styles.header}>
        <h3 className={styles.name}>{item.name}</h3>
        <span className={styles.price}>
          {item.option_groups.length > 0 && 'from '}
          {item.price_sar} SAR
        </span>
      </header>
      <p className={styles.description}>{item.description}</p>
      <ItemBadges item={item} />
      <p className={styles.ingredients}>{item.ingredients.join(', ')}</p>
      {item.pack_size > 1 && (
        <p className={styles.traces}>
          Sold in packs of {item.pack_size} {item.pack_unit ?? 'pieces'}.
        </p>
      )}
      <ItemOptions groups={item.option_groups} removable={item.removable} />
      <div className={styles.allergens}>
        <span className={styles.allergenTitle}>Allergens:</span>
        {item.allergens.length === 0 ? (
          <span className={styles.none}>none listed</span>
        ) : (
          item.allergens.map((a) => (
            <span key={a} className={styles.chip}>
              {allergenLabel(a)}
            </span>
          ))
        )}
      </div>
      {item.may_contain_warnings.length > 0 && (
        <p className={styles.warning} role="note">
          May contain {item.may_contain_warnings.map(allergenLabel).join(', ')}, which you avoid.
          Please check with staff.
        </p>
      )}
      {item.taste_notes.length > 0 && (
        <p className={styles.traces}>Not your usual: {item.taste_notes.join('; ')}.</p>
      )}
      {traces.length > 0 && (
        <p className={styles.traces}>
          May contain traces of {traces.map(allergenLabel).join(', ')}.
        </p>
      )}
      {quickAdd && canQuickAdd(item) ? (
        <button
          className={styles.choose}
          type="button"
          aria-label={addLabel(item, quickAdd)}
          disabled={quickAdd.pending !== null}
          onClick={() => quickAdd.add(item)}
        >
          {quickAdd.added === item.id ? 'Added ✓' : 'Add'}
        </button>
      ) : (
        onChoose && (
          <button className={styles.choose} type="button" onClick={onChoose}>
            {item.option_groups.length > 0 ? 'Choose options' : 'Add to cart'}
          </button>
        )
      )}
    </article>
  )
}

export default ItemCard
