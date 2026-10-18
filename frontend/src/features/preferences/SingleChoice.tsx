import { useState } from 'react'

import type { Preference } from '../../api/types'
import { LABELS, plainLabel } from '../memory/memoryLabels'
import ConfirmBox from './ConfirmBox'
import styles from './Preferences.module.css'
import type { Edits } from './usePreferences'

interface Props {
  kind: 'diet' | 'spice'
  hint: string
  /** Least to most strict: for a hard rule, a move to the left asks first. */
  options: string[]
  current: Preference | undefined
  edits: Edits
  enforced?: boolean
}

type Choice = string | null

/** A kind with at most one value (diet, spice): a new pick replaces the old one,
 * as when the guest corrects it in the chat. */
function SingleChoice({ kind, hint, options, current, edits, enforced }: Props) {
  const [pending, setPending] = useState<{ value: Choice } | null>(null)
  const save = (value: Choice) => {
    setPending(null)
    if (value === null) {
      if (current) void edits.remove(current.id)
    } else {
      void (current ? edits.change(current.id, value) : edits.add(kind, value))
    }
  }
  const choose = (value: Choice) => {
    const loosens =
      current !== undefined &&
      (value === null || options.indexOf(value) < options.indexOf(current.value))
    if (enforced && loosens) setPending({ value })
    else save(value)
  }
  const name = (value: Choice) => (value === null ? 'No preference' : plainLabel(value))
  return (
    <fieldset className={styles.section} disabled={edits.busy}>
      <legend className={styles.heading}>
        {LABELS[kind]}
        {enforced && <span className={styles.enforced}>always enforced</span>}
      </legend>
      <p className={styles.hint}>{hint}</p>
      <div className={styles.options}>
        {[null, ...options].map((value) => (
          <label key={value ?? ''} className={styles.option}>
            <input
              type="radio"
              name={kind}
              checked={(current?.value ?? null) === value}
              onChange={() => choose(value)}
            />
            {name(value)}
          </label>
        ))}
      </div>
      {pending && current && (
        <ConfirmBox
          message={`Change your ${LABELS[kind].toLowerCase()} from ${current.value} to ${name(pending.value).toLowerCase()}? Dishes that do not fit ${current.value} will be recommended again.`}
          action="Change it"
          onKeep={() => setPending(null)}
          onConfirm={() => save(pending.value)}
        />
      )}
    </fieldset>
  )
}

export default SingleChoice
