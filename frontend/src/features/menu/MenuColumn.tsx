import { Link } from 'react-router'

import type { Card, GuestMenu } from '../../api/menuTypes'
import Skeleton from '../../components/Skeleton'
import type { QuickAdd } from '../chat/quickAdd'
import MenuBrowser from './MenuBrowser'
import styles from './MenuColumn.module.css'
import MenuHeader from './MenuHeader'

interface Props {
  menu: GuestMenu | null
  error: string | null
  onRetry: () => void
  onChoose: (item: Card) => void
  quickAdd: QuickAdd
}

/** The restaurant's side of the page: its header, then the menu, a skeleton, or an error. */
function MenuColumn({ menu, error, onRetry, onChoose, quickAdd }: Props) {
  return (
    <div className={styles.menu}>
      <MenuHeader restaurant={menu?.restaurant ?? null} />
      {error && (
        <div className={styles.error} role="alert">
          <span>{error}</span>
          <button type="button" onClick={onRetry}>
            Retry
          </button>
          <Link to="/">All restaurants</Link>
        </div>
      )}
      {!menu && !error && <Skeleton count={6} label="Loading the menu" />}
      {menu && <MenuBrowser menu={menu} onChoose={onChoose} quickAdd={quickAdd} />}
    </div>
  )
}

export default MenuColumn
