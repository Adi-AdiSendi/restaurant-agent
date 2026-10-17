import type { Restaurant } from '../../api/types'
import RestaurantPicker from '../restaurants/RestaurantPicker'
import styles from './ChatHeader.module.css'

interface Props {
  username: string
  restaurants: Restaurant[]
  current: Restaurant | null
  /** A reply is pending: a new chat now would receive the old reply. */
  busy: boolean
  onChoose: (slug: string) => void
  onNewChat: () => void
  onLogout: () => void
}

function ChatHeader({
  username,
  restaurants,
  current,
  busy,
  onChoose,
  onNewChat,
  onLogout,
}: Props) {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <img className={styles.logo} src="/foodics-logo.svg" alt="Foodics" />
        <div className={styles.titles}>
          <span className={styles.restaurant}>
            {current && (
              <span
                className={styles.dot}
                style={{ background: current.accent_color }}
                aria-hidden="true"
              />
            )}
            {current?.name ?? 'Foodics Order Assistant'}
          </span>
          <span className={styles.powered}>Foodics Order Assistant</span>
        </div>
      </div>
      <div className={styles.actions}>
        <RestaurantPicker
          restaurants={restaurants}
          current={current}
          disabled={busy}
          onChoose={onChoose}
        />
        <span className={styles.user}>Hi, {username}</span>
        <button className={styles.primary} type="button" onClick={onNewChat} disabled={busy}>
          New chat
        </button>
        <button className={styles.ghost} type="button" onClick={onLogout}>
          Log out
        </button>
      </div>
    </header>
  )
}

export default ChatHeader
