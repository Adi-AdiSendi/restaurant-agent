import { useCallback, useState } from 'react'

import MemoryPanel from '../memory/MemoryPanel'
import ChatHeader from './ChatHeader'
import styles from './ChatPage.module.css'
import Composer from './Composer'
import MessageList from './MessageList'
import Suggestions from './Suggestions'
import { useChat } from './useChat'

interface Props {
  username: string
  isNew: boolean
  onLogout: () => void
}

function ChatPage({ username, isNew, onLogout }: Props) {
  const [refreshKey, setRefreshKey] = useState(0)
  const onReplied = useCallback(() => setRefreshKey((k) => k + 1), [])
  const { state, send, retry, newChat } = useChat({ onUnauthorized: onLogout, onReplied })

  const greeting = isNew
    ? `Welcome, ${username}! Tell me what you feel like, and anything you avoid or cannot eat. I will remember it for next time.`
    : `Welcome back, ${username}! What are you in the mood for today?`

  return (
    <div className={styles.page}>
      <ChatHeader
        username={username}
        busy={state.sending}
        onNewChat={() => void newChat()}
        onLogout={onLogout}
      />
      <div className={styles.body}>
        <main className={styles.chat}>
          <MessageList messages={state.messages} sending={state.sending} greeting={greeting} />
          {state.error && (
            <div className={styles.error} role="alert">
              <span>{state.error}</span>
              {state.retry && (
                <button className={styles.retry} type="button" onClick={retry}>
                  Retry
                </button>
              )}
            </div>
          )}
          {state.messages.length === 0 && !state.sending && (
            <Suggestions onPick={(text) => void send(text)} />
          )}
          <Composer
            disabled={state.sending || state.conversationId === null}
            onSend={(text) => void send(text)}
          />
        </main>
        <MemoryPanel refreshKey={refreshKey} onUnauthorized={onLogout} />
      </div>
    </div>
  )
}

export default ChatPage
