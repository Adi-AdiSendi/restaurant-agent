import { useState } from 'react'

import type { Card, GuestMenu } from '../../api/menuTypes'
import ItemCard from '../chat/ItemCard'
import type { QuickAdd } from '../chat/quickAdd'
import styles from './MenuBrowser.module.css'

const label = (category: string) => {
  const words = category.replaceAll('_', ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

interface Props {
  menu: GuestMenu
  onChoose: (item: Card) => void
  quickAdd?: QuickAdd
}

/** Category tabs, a search, and a filter for dishes that suit the guest's saved profile. */
function MenuBrowser({ menu, onChoose, quickAdd }: Props) {
  const [category, setCategory] = useState<string | null>(null)
  const [text, setText] = useState('')
  const [fitsOnly, setFitsOnly] = useState(false)
  const [tastesOnly, setTastesOnly] = useState(false)
  const needle = text.trim().toLowerCase()
  const shown = menu.items.filter(
    (item) =>
      (category === null || item.category === category) &&
      (!fitsOnly || item.conflicts_with_guest.length === 0) &&
      (!tastesOnly || item.taste_notes.length === 0) &&
      (needle === '' ||
        [item.name, item.description, ...item.ingredients]
          .join(' ')
          .toLowerCase()
          .includes(needle)),
  )
  return (
    <section className={styles.browser} aria-label="Menu">
      <div className={styles.tabs} role="group" aria-label="Categories">
        {[null, ...menu.restaurant.categories].map((c) => (
          <button
            key={c ?? 'all'}
            type="button"
            className={c === category ? styles.tabOn : styles.tab}
            aria-pressed={c === category}
            onClick={() => setCategory(c)}
          >
            {c === null ? 'All' : label(c)}
          </button>
        ))}
      </div>
      <div className={styles.filters}>
        <input
          className={styles.search}
          type="search"
          placeholder="Search dishes or ingredients"
          aria-label="Search the menu"
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
        <label className={styles.fits}>
          <input
            type="checkbox"
            checked={fitsOnly}
            onChange={(e) => setFitsOnly(e.target.checked)}
          />
          Fits my profile
        </label>
        <label className={styles.fits}>
          <input
            type="checkbox"
            checked={tastesOnly}
            onChange={(e) => setTastesOnly(e.target.checked)}
          />
          Matches my tastes
        </label>
      </div>
      {shown.length === 0 && <p className={styles.empty}>No dishes match.</p>}
      <div className={styles.grid}>
        {shown.map((item) => (
          <ItemCard key={item.id} item={item} onChoose={() => onChoose(item)} quickAdd={quickAdd} />
        ))}
      </div>
    </section>
  )
}

export default MenuBrowser
