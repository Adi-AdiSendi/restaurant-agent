import CaloriesToday from '../memory/CaloriesToday'
import { LABELS } from '../memory/memoryLabels'
import AmountField from './AmountField'
import SingleChoice from './SingleChoice'
import { ofKind, type SectionProps } from './usePreferences'

/** Spice, budget and the calorie goal: soft, so dishes are marked, never blocked. */
function SoftLimits({ active, vocab, edits }: SectionProps) {
  const budget = ofKind(active, 'budget')[0]
  const calories = ofKind(active, 'calories')[0]
  return (
    <>
      <SingleChoice
        kind="spice"
        hint="Spicier dishes are marked, not hidden."
        options={vocab.spice_levels}
        current={ofKind(active, 'spice')[0]}
        edits={edits}
      />
      <AmountField
        key={`budget-${budget?.value ?? ''}`}
        kind="budget"
        title={LABELS.budget}
        hint="Dishes over it are marked."
        unit="SAR"
        step={0.01}
        current={budget}
        edits={edits}
      />
      <AmountField
        key={`calories-${calories?.value ?? ''}`}
        kind="calories"
        title={LABELS.calories}
        hint="Counted from the estimates of today's orders. Dishes over what is left are marked."
        unit="kcal"
        min={vocab.calories_min}
        max={vocab.calories_max}
        step={1}
        current={calories}
        edits={edits}
      >
        {calories && <CaloriesToday goal={Number(calories.value)} refreshKey={0} />}
      </AmountField>
    </>
  )
}

export default SoftLimits
