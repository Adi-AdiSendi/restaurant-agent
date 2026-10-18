import { useState } from 'react'

import type { Preference } from '../../api/types'
import { LABELS, plainLabel } from '../memory/memoryLabels'
import ConfirmBox from './ConfirmBox'
import styles from './Preferences.module.css'
import type { Edits } from './usePreferences'

interface Props {
  allergens: string[]
  rows: Preference[]
  edits: Edits
}

/** Allergies are hard rules, enforced in code. Removing one asks first. */
function AllergyList({ allergens, rows, edits }: Props) {
  const [confirm, setConfirm] = useState<Preference | null>(null)
  const saved = new Map(rows.map((row) => [row.value, row]))
  const remove = (row: Preference) => {
    setConfirm(null)
    void edits.remove(row.id)
  }
  return (
    <fieldset className={styles.section} disabled={edits.busy}>
      <legend className={styles.heading}>
        {LABELS.allergy} <span className={styles.enforced}>always enforced</span>
      </legend>
      <p className={styles.hint}>
        Dishes with these are never recommended, and adding one to your cart asks you first.
      </p>
      <div className={styles.options}>
        {allergens.map((allergen) => {
          const row = saved.get(allergen)
          return (
            <label key={allergen} className={styles.option}>
              <input
                type="checkbox"
                checked={row !== undefined}
                onChange={() => (row ? setConfirm(row) : void edits.add('allergy', allergen))}
              />
              {plainLabel(allergen)}
            </label>
          )
        })}
      </div>
      {confirm && (
        <ConfirmBox
          message={`Remove your ${plainLabel(confirm.value).toLowerCase()} allergy? Dishes with it will be recommended again.`}
          action="Remove"
          onKeep={() => setConfirm(null)}
          onConfirm={() => remove(confirm)}
        />
      )}
    </fieldset>
  )
}

export default AllergyList
