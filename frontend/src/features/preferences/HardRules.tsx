import AllergyList from './AllergyList'
import SingleChoice from './SingleChoice'
import { ofKind, type SectionProps } from './usePreferences'

/** Allergies and diet: the only rules enforced in code (ADR 0009). */
function HardRules({ active, vocab, edits }: SectionProps) {
  return (
    <>
      <AllergyList allergens={vocab.allergens} rows={ofKind(active, 'allergy')} edits={edits} />
      <SingleChoice
        kind="diet"
        hint="Only dishes that fit are recommended."
        options={vocab.diets}
        current={ofKind(active, 'diet')[0]}
        edits={edits}
        enforced
      />
    </>
  )
}

export default HardRules
