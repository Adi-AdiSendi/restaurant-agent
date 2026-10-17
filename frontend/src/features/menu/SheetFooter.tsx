import styles from './ItemSheet.module.css'

const clamp = (value: string) => Math.min(20, Math.max(1, Number(value) || 1))

interface Props {
  quantity: number
  onQuantity: (quantity: number) => void
  /** "Add to cart · 19.00 SAR", or what is still missing ("Choose a milk"). */
  label: string
  disabled: boolean
  onAdd: () => void
}

function SheetFooter({ quantity, onQuantity, label, disabled, onAdd }: Props) {
  return (
    <footer className={styles.foot}>
      <label className={styles.quantity}>
        Quantity
        <input
          type="number"
          min={1}
          max={20}
          value={quantity}
          onChange={(e) => onQuantity(clamp(e.target.value))}
        />
      </label>
      <button className={styles.add} type="button" disabled={disabled} onClick={onAdd}>
        {label}
      </button>
    </footer>
  )
}

export default SheetFooter
