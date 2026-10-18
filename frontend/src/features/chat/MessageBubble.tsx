import type { Card } from '../../api/menuTypes'
import ActionCard from './ActionCard'
import type { ChatMessage } from './chatTypes'
import ItemCard from './ItemCard'
import styles from './MessageBubble.module.css'

interface Props {
  message: ChatMessage
  onChoose?: (item: Card) => void
}

function MessageBubble({ message, onChoose }: Props) {
  const mine = message.role === 'user'
  return (
    <div className={mine ? styles.rowMine : styles.row}>
      <div className={mine ? styles.mine : styles.theirs}>{message.text}</div>
      {message.items.length > 0 && (
        <div className={styles.cards}>
          {message.items.map((item) => (
            <ItemCard key={item.id} item={item} onChoose={onChoose && (() => onChoose(item))} />
          ))}
        </div>
      )}
      {message.actions.map((action, n) => (
        <ActionCard key={n} action={action} />
      ))}
    </div>
  )
}

export default MessageBubble
