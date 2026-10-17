import type { Allergen, Card } from '../../api/menuTypes'
import styles from './ItemCard.module.css'
import ItemOptions from './ItemOptions'

const SPICE = ['Not spicy', 'Mild', 'Medium', 'Hot']

const allergenLabel = (allergen: Allergen) => allergen.replace('_', ' ')

interface Props {
  item: Card
  /** Opens the options sheet, so the guest can add it to the cart. */
  onChoose?: () => void
}

// Every detail comes from the card data the backend loaded from the database,
// never from the assistant's text. Allergens are always visible.
function ItemCard({ item, onChoose }: Props) {
  const diet = item.is_vegan ? 'Vegan' : item.is_vegetarian ? 'Vegetarian' : null
  const traces = item.may_contain.filter((a) => !item.may_contain_warnings.includes(a))
  return (
    <article className={styles.card} aria-label={item.name}>
      <header className={styles.header}>
        <h3 className={styles.name}>{item.name}</h3>
        <span className={styles.price}>
          {item.option_groups.length > 0 && 'from '}
          {item.price_sar} SAR
        </span>
      </header>
      <p className={styles.description}>{item.description}</p>
      <div className={styles.badges}>
        {diet && <span className={styles.diet}>{diet}</span>}
        <span className={styles.spice}>
          <span aria-hidden="true">{'🌶'.repeat(item.spice_level)}</span>{' '}
          {SPICE[item.spice_level] ?? ''}
        </span>
      </div>
      <p className={styles.ingredients}>{item.ingredients.join(', ')}</p>
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
      {traces.length > 0 && (
        <p className={styles.traces}>
          May contain traces of {traces.map(allergenLabel).join(', ')}.
        </p>
      )}
      {onChoose && (
        <button className={styles.choose} type="button" onClick={onChoose}>
          {item.option_groups.length > 0 ? 'Choose options' : 'Add to cart'}
        </button>
      )}
    </article>
  )
}

export default ItemCard
