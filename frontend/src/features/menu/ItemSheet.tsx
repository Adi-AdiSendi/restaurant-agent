import { useState } from 'react'

import type { Card } from '../../api/menuTypes'
import { useModal } from '../../components/useModal'
import AddConfirm from './AddConfirm'
import ChoiceExtras from './ChoiceExtras'
import {
  chosenConflicts,
  initialChoice,
  linePrice,
  missing,
  toggleOption,
  toggleRemoved,
} from './choice'
import styles from './ItemSheet.module.css'
import OptionGroupField from './OptionGroupField'
import SheetFooter from './SheetFooter'
import { useAddLine } from './useAddLine'

interface Props {
  item: Card
  restaurant: string
  onClose: () => void
  onUnauthorized: () => void
}

/** Configure one dish and add it to the cart. The server re-prices and re-checks it. */
function ItemSheet({ item, restaurant, onClose, onUnauthorized }: Props) {
  const [choice, setChoice] = useState(() => initialChoice(item))
  const dialog = useModal<HTMLDivElement>(onClose)
  const add = useAddLine({ item, restaurant, choice, onAdded: onClose, onUnauthorized })
  const todo = missing(item, choice)
  const conflicts = chosenConflicts(item, choice)

  return (
    <div className={styles.backdrop} onClick={onClose}>
      <div
        ref={dialog}
        className={styles.sheet}
        role="dialog"
        aria-modal="true"
        aria-labelledby="sheet-title"
        onClick={(e) => e.stopPropagation()}
      >
        <header className={styles.head}>
          <h2 id="sheet-title" className={styles.title}>
            {item.name}
          </h2>
          <button className={styles.close} type="button" onClick={onClose} aria-label="Close">
            ×
          </button>
        </header>
        <p className={styles.description}>{item.description}</p>
        {item.option_groups.map((group) => (
          <OptionGroupField
            key={group.id}
            group={group}
            chosen={choice.optionIds}
            onToggle={(id) => setChoice((c) => toggleOption(c, group, id))}
          />
        ))}
        <ChoiceExtras
          removable={item.removable}
          choice={choice}
          onToggleRemoved={(ingredient) => setChoice((c) => toggleRemoved(c, ingredient))}
        />
        {conflicts.length > 0 && (
          <p className={styles.warning} role="note">
            As chosen, this is not suitable for you: {conflicts.join(', ')}.
          </p>
        )}
        {add.ask && (
          <AddConfirm ask={add.ask} busy={add.busy} onYes={add.confirm} onNo={add.cancel} />
        )}
        {add.error && (
          <p className={styles.error} role="alert">
            {add.error}
          </p>
        )}
        <SheetFooter
          quantity={choice.quantity}
          onQuantity={(quantity) => setChoice((c) => ({ ...c, quantity }))}
          label={todo[0] ?? `Add to cart · ${linePrice(item, choice)} SAR`}
          disabled={todo.length > 0 || add.busy || add.ask !== null}
          onAdd={add.submit}
        />
      </div>
    </div>
  )
}

export default ItemSheet
