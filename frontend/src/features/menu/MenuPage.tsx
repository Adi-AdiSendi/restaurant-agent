import { useCallback, useState } from 'react'
import { Link, useParams } from 'react-router'

import type { Card } from '../../api/menuTypes'
import { useCart } from '../cart/cartContext'
import ChatPanel from '../chat/ChatPanel'
import MemoryPanel from '../memory/MemoryPanel'
import ItemSheet from './ItemSheet'
import MenuBrowser from './MenuBrowser'
import styles from './MenuPage.module.css'
import { useGuestMenu } from './useGuestMenu'

interface Props {
  username: string
  isNew: boolean
  onLogout: () => void
}

type Side = 'chat' | 'memory'

/** One restaurant: its menu, the chat scoped to it by the URL, and the guest's memory. */
function MenuPage({ username, isNew, onLogout }: Props) {
  const { slug = '' } = useParams()
  const [refreshKey, setRefreshKey] = useState(0)
  const { refresh: refreshCart } = useCart()
  const onReplied = useCallback(() => {
    setRefreshKey((k) => k + 1)
    void refreshCart()
  }, [refreshCart])
  const { menu, error, reload } = useGuestMenu(slug, refreshKey, onLogout)
  const [choosing, setChoosing] = useState<Card | null>(null)
  const [side, setSide] = useState<Side>('chat')

  return (
    <div className={styles.page}>
      <div className={styles.menu}>
        <header className={styles.head} style={{ borderLeftColor: menu?.restaurant.accent_color }}>
          <h1 className={styles.title}>{menu?.restaurant.name ?? ' '}</h1>
          {menu && <p className={styles.tagline}>{menu.restaurant.tagline}</p>}
        </header>
        {error && (
          <div className={styles.error} role="alert">
            <span>{error}</span>
            <button type="button" onClick={() => void reload()}>
              Retry
            </button>
            <Link to="/">All restaurants</Link>
          </div>
        )}
        {menu && <MenuBrowser menu={menu} onChoose={setChoosing} />}
      </div>
      <aside className={styles.side}>
        <div className={styles.sideTabs} role="group" aria-label="Assistant">
          {(['chat', 'memory'] as const).map((tab) => (
            <button
              key={tab}
              type="button"
              aria-pressed={side === tab}
              className={side === tab ? styles.sideTabOn : styles.sideTab}
              onClick={() => setSide(tab)}
            >
              {tab === 'chat' ? 'Chat' : 'What I remember'}
            </button>
          ))}
        </div>
        <div className={side === 'chat' ? styles.sideBody : styles.hidden}>
          <ChatPanel
            restaurant={slug}
            username={username}
            isNew={isNew}
            onUnauthorized={onLogout}
            onReplied={onReplied}
            onChoose={setChoosing}
          />
        </div>
        {side === 'memory' && <MemoryPanel refreshKey={refreshKey} onUnauthorized={onLogout} />}
      </aside>
      {choosing && (
        <ItemSheet
          item={choosing}
          restaurant={slug}
          onClose={() => setChoosing(null)}
          onUnauthorized={onLogout}
        />
      )}
    </div>
  )
}

export default MenuPage
