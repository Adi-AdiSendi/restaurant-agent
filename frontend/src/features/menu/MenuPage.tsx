import { type CSSProperties, useCallback, useState } from 'react'

import type { Card } from '../../api/menuTypes'
import type { ChatReply } from '../../api/types'
import { useCart } from '../cart/cartContext'
import ChatPanel from '../chat/ChatPanel'
import MemoryPanel from '../memory/MemoryPanel'
import ItemSheet from './ItemSheet'
import MenuColumn from './MenuColumn'
import styles from './MenuPage.module.css'
import { useGuestMenu } from './useGuestMenu'
import { useQuickAdd } from './useQuickAdd'

interface Props {
  slug: string
  username: string
  isNew: boolean
  onLogout: () => void
}

type Side = 'chat' | 'memory'

/** One restaurant: its menu, the chat scoped to it by the URL, and the guest's memory. */
function MenuPage({ slug, username, isNew, onLogout }: Props) {
  const [refreshKey, setRefreshKey] = useState(0)
  const { setCart } = useCart()
  const onReplied = useCallback(
    (reply: ChatReply) => {
      setRefreshKey((k) => k + 1)
      setCart(reply.cart)
    },
    [setCart],
  )
  const { menu, error, reload } = useGuestMenu(slug, refreshKey, onLogout)
  const [choosing, setChoosing] = useState<Card | null>(null)
  const [side, setSide] = useState<Side>('chat')
  const quickAdd = useQuickAdd({
    restaurant: slug,
    onNeedsSheet: setChoosing,
    onUnauthorized: onLogout,
  })
  // Photos, icons and the header use the restaurant's own colour.
  const accent = { '--accent': menu?.restaurant.accent_color } as CSSProperties

  return (
    <div className={styles.page} style={accent}>
      <MenuColumn
        menu={menu}
        error={error}
        onRetry={() => void reload()}
        onChoose={setChoosing}
        quickAdd={quickAdd}
      />
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
            quickAdd={quickAdd}
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
