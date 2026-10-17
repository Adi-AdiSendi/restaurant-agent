import type { Choice } from './choice'
import styles from './OptionGroupField.module.css'

interface Props {
  removable: string[]
  choice: Choice
  onToggleRemoved: (ingredient: string) => void
}

/** Ingredients the guest may leave out. Leaving one out never removes an allergen. */
function ChoiceExtras({ removable, choice, onToggleRemoved }: Props) {
  if (removable.length === 0) return null
  return (
    <fieldset className={styles.group}>
      <legend className={styles.legend}>Leave out</legend>
      {removable.map((ingredient) => (
        <label key={ingredient} className={styles.option}>
          <input
            type="checkbox"
            checked={choice.removed.includes(ingredient)}
            onChange={() => onToggleRemoved(ingredient)}
          />
          <span className={styles.optionName}>No {ingredient}</span>
        </label>
      ))}
      <p className={styles.hint}>Leaving something out does not remove an allergen.</p>
    </fieldset>
  )
}

export default ChoiceExtras
