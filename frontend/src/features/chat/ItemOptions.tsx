import type { Allergen, OptionGroup } from '../../api/types'
import styles from './ItemOptions.module.css'

const allergenLabel = (allergen: Allergen) => allergen.replace('_', ' ')
const SPICE = ['', 'mild', 'medium', 'hot']

function rule({ min_choices: min, max_choices: max }: OptionGroup): string {
  if (min === 0) return max === 1 ? 'optional' : `optional, up to ${max}`
  return min === max ? `choose ${min}` : `choose ${min} to ${max}`
}

interface Props {
  groups: OptionGroup[]
  removable: string[]
}

// Every option shows its own allergens; ones that break the guest's saved
// allergies or diet are struck through with the reason.
function ItemOptions({ groups, removable }: Props) {
  if (groups.length === 0 && removable.length === 0) return null
  return (
    <div className={styles.options}>
      {groups.map((group) => (
        <div key={group.id} className={styles.group}>
          <span className={styles.groupName}>
            {group.name} <span className={styles.rule}>({rule(group)})</span>
          </span>
          <ul className={styles.list}>
            {group.options.map((option) => {
              const conflicts = option.conflicts_with_guest
              const extra = Number(option.price_delta_sar) > 0 ? ` +${option.price_delta_sar}` : ''
              return (
                <li key={option.id} className={conflicts.length ? styles.conflict : styles.option}>
                  <span className={styles.optionName}>
                    {option.name}
                    {extra}
                  </span>
                  {option.spice_level > 0 && (
                    <span className={styles.contains}> {SPICE[option.spice_level]}</span>
                  )}
                  {option.allergens.length > 0 && (
                    <span className={styles.contains}>
                      {' '}
                      contains {option.allergens.map(allergenLabel).join(', ')}
                    </span>
                  )}
                  {option.may_contain_warnings.length > 0 && (
                    <span className={styles.reason}>
                      {' '}
                      may contain {option.may_contain_warnings.map(allergenLabel).join(', ')}
                    </span>
                  )}
                  {conflicts.length > 0 && (
                    <span className={styles.reason}> not for you: {conflicts.join(', ')}</span>
                  )}
                </li>
              )
            })}
          </ul>
        </div>
      ))}
      {removable.length > 0 && (
        <p className={styles.removable}>Can be made without: {removable.join(', ')}.</p>
      )}
    </div>
  )
}

export default ItemOptions
