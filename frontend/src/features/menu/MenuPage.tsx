import { useCallback, useState } from 'react'
import { useParams } from 'react-router'

import ChatPanel from '../chat/ChatPanel'
import MemoryPanel from '../memory/MemoryPanel'
import styles from './MenuPage.module.css'

interface Props {
  username: string
  isNew: boolean
  onLogout: () => void
}

/** One restaurant: the chat (scoped to it by the URL) and what the assistant remembers. */
function MenuPage({ username, isNew, onLogout }: Props) {
  const { slug = '' } = useParams()
  const [refreshKey, setRefreshKey] = useState(0)
  const onReplied = useCallback(() => setRefreshKey((k) => k + 1), [])
  return (
    <div className={styles.page}>
      <ChatPanel
        restaurant={slug}
        username={username}
        isNew={isNew}
        onUnauthorized={onLogout}
        onReplied={onReplied}
      />
      <MemoryPanel refreshKey={refreshKey} onUnauthorized={onLogout} />
    </div>
  )
}

export default MenuPage
