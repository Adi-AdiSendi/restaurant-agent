import styles from './ChatHeader.module.css'

interface Props {
  username: string
  /** A reply is pending: a new chat now would receive the old reply. */
  busy: boolean
  onNewChat: () => void
  onLogout: () => void
}

function ChatHeader({ username, busy, onNewChat, onLogout }: Props) {
  return (
    <header className={styles.header}>
      <div className={styles.brand}>
        <img className={styles.logo} src="/foodics-logo.svg" alt="Foodics" />
        <div className={styles.titles}>
          <span className={styles.restaurant}>Corner Table</span>
          <span className={styles.powered}>Powered by Foodics</span>
        </div>
      </div>
      <div className={styles.actions}>
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
