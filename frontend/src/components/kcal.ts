// Calories are estimates (ADR 0025), so every place that shows them says so.
export function kcalLabel(kcal: number | null | undefined): string | null {
  return kcal ? `about ${kcal.toLocaleString('en')} kcal (estimate)` : null
}
