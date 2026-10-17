import styles from './Suggestions.module.css'

const PROMPTS = [
  'Something vegan under 45 SAR',
  'I am allergic to peanuts',
  'What is good and spicy?',
  'A light dessert, please',
]

interface Props {
  onPick: (text: string) => void
}

function Suggestions({ onPick }: Props) {
  return (
    <div className={styles.row} role="group" aria-label="Suggestions">
      {PROMPTS.map((prompt) => (
        <button key={prompt} className={styles.chip} type="button" onClick={() => onPick(prompt)}>
          {prompt}
        </button>
      ))}
    </div>
  )
}

export default Suggestions
