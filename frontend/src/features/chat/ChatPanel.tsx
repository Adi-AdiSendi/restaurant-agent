import type { Card } from '../../api/menuTypes'
import type { ChatReply } from '../../api/types'
import Composer from './Composer'
import type { QuickAdd } from './quickAdd'
import MessageList from './MessageList'
import styles from './ChatPanel.module.css'
import Suggestions from './Suggestions'
import { useChat } from './useChat'

interface Props {
  /** The restaurant's slug. A new one starts a new conversation there. */
  restaurant: string
  username: string
  isNew: boolean
  onUnauthorized: () => void
  onReplied: (reply: ChatReply) => void
  /** Opens the options sheet for a recommended dish. */
  onChoose?: (item: Card) => void
  /** One-click add for cards and menu blocks. */
  quickAdd?: QuickAdd
}

function ChatPanel(props: Props) {
  const { restaurant, username, isNew, onUnauthorized, onReplied, onChoose, quickAdd } = props
  const { state, send, retry, newChat } = useChat({ restaurant, onUnauthorized, onReplied })
  const greeting = isNew
    ? `Welcome, ${username}! Tell me what you feel like, and anything you avoid or cannot eat. I will remember it for next time.`
    : `Welcome back, ${username}! What are you in the mood for today?`

  return (
    <section className={styles.chat} aria-label="Chat with the assistant">
      <div className={styles.bar}>
        <h2 className={styles.title}>Ask the assistant</h2>
        <button
          className={styles.newChat}
          type="button"
          onClick={() => void newChat()}
          disabled={state.sending}
        >
          New chat
        </button>
      </div>
      <MessageList
        messages={state.messages}
        sending={state.sending}
        greeting={greeting}
        onChoose={onChoose}
        quickAdd={quickAdd}
      />
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
    </section>
  )
}

export default ChatPanel
