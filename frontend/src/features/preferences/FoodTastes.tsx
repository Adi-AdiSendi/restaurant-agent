import { LABELS } from '../memory/memoryLabels'
import DayRules from './DayRules'
import { ofKind, type SectionProps } from './usePreferences'
import WordList from './WordList'

/** Foods liked and disliked, always or on one weekday. Soft: nothing is blocked. */
function FoodTastes({ active, vocab, edits }: SectionProps) {
  return (
    <>
      <WordList
        kind="like"
        title={LABELS.like}
        hint="Dishes with these get a badge."
        placeholder="salmon"
        rows={ofKind(active, 'like')}
        edits={edits}
      />
      <WordList
        kind="dislike"
        title={LABELS.dislike}
        hint="Dishes where it cannot be left out are marked. The chat leaves it out when it can."
        placeholder="pickles"
        rows={ofKind(active, 'dislike')}
        edits={edits}
      />
      <DayRules
        kind="day_dislike"
        title={LABELS.day_dislike}
        hint="On that day the food works like a dislike."
        weekdays={vocab.weekdays}
        rows={ofKind(active, 'day_dislike')}
        edits={edits}
      />
      <DayRules
        kind="day_like"
        title={LABELS.day_like}
        hint="On that day dishes with it are marked as today's pick."
        weekdays={vocab.weekdays}
        rows={ofKind(active, 'day_like')}
        edits={edits}
      />
    </>
  )
}

export default FoodTastes
