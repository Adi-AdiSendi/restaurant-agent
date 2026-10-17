import type { Allergen, OptionGroup } from '../../api/menuTypes'
import styles from './OptionGroupField.module.css'

const label = (a: Allergen) => a.replace('_', ' ')

function rule({ min_choices: min, max_choices: max }: OptionGroup): string {
  if (min === 0) return max === 1 ? 'optional' : `optional, up to ${max}`
  return min === max ? `choose ${min}` : `choose ${min} to ${max}`
}

interface Props {
  group: OptionGroup
  chosen: number[]
  onToggle: (optionId: number) => void
}

/** One option group: radio buttons for a single choice, checkboxes otherwise. */
function OptionGroupField({ group, chosen, onToggle }: Props) {
  const single = group.max_choices === 1
  return (
    <fieldset className={styles.group}>
      <legend className={styles.legend}>
        {group.name} <span className={styles.rule}>({rule(group)})</span>
      </legend>
      {group.options.map((option) => {
        const conflicts = option.conflicts_with_guest
        const extra = Number(option.price_delta_sar) > 0 ? `+${option.price_delta_sar}` : ''
        return (
          <label key={option.id} className={conflicts.length ? styles.conflict : styles.option}>
            <input
              type={single ? 'radio' : 'checkbox'}
              name={`group-${group.id}`}
              checked={chosen.includes(option.id)}
              onChange={() => onToggle(option.id)}
            />
            <span className={styles.optionName}>{option.name}</span>
            <span className={styles.optionMeta}>
              {extra}
              {option.allergens.length > 0 && ` contains ${option.allergens.map(label).join(', ')}`}
              {option.may_contain_warnings.length > 0 &&
                ` may contain ${option.may_contain_warnings.map(label).join(', ')}`}
            </span>
            {conflicts.length > 0 && (
              <span className={styles.reason}>not for you: {conflicts.join(', ')}</span>
            )}
          </label>
        )
      })}
    </fieldset>
  )
}

export default OptionGroupField
