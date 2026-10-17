import { useEffect, useRef } from 'react'

import type { Card } from '../../api/menuTypes'
import type { ChatMessage } from './chatReducer'
import MessageBubble from './MessageBubble'
import styles from './MessageList.module.css'

interface Props {
  messages: ChatMessage[]
  sending: boolean
  greeting: string
  onChoose?: (item: Card) => void
}

function MessageList({ messages, sending, greeting, onChoose }: Props) {
  const end = useRef<HTMLDivElement>(null)

  useEffect(() => {
    end.current?.scrollIntoView?.({ behavior: 'smooth', block: 'end' })
  }, [messages.length, sending])

  return (
    <div className={styles.list} aria-live="polite">
      <MessageBubble message={{ id: 0, role: 'assistant', text: greeting, items: [] }} />
      {messages.map((message) => (
        <MessageBubble key={message.id} message={message} onChoose={onChoose} />
      ))}
      {sending && (
        <div className={styles.typing} role="status" aria-label="The assistant is thinking">
          <span />
          <span />
          <span />
        </div>
      )}
      <div ref={end} />
    </div>
  )
}

export default MessageList
