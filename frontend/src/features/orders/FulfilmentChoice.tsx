import { useId } from 'react'

import type { Fulfilment } from '../../api/cartTypes'
import styles from './Orders.module.css'

const LABELS: Record<Fulfilment, string> = { pickup: 'Pickup', dine_in: 'Dine in' }

interface Props {
  value: Fulfilment
  onChange: (value: Fulfilment) => void
}

function FulfilmentChoice({ value, onChange }: Props) {
  // Unique per use: the checkout page and chat checkout cards each have their own group.
  const name = useId()
  return (
    <fieldset className={styles.choice}>
      <legend>How would you like it?</legend>
      {(['pickup', 'dine_in'] as const).map((option) => (
        <label key={option}>
          <input
            type="radio"
            name={name}
            checked={value === option}
            onChange={() => onChange(option)}
          />{' '}
          {LABELS[option]}
        </label>
      ))}
    </fieldset>
  )
}

export default FulfilmentChoice
