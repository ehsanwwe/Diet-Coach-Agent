import type { NutritionPlanResponse } from '@/types/nutrition'
import type { Dictionary } from '@/dictionaries/fa'

interface Props {
  plan: NutritionPlanResponse
  dict: Pick<Dictionary, 'plan'>
}

const MEAL_TIME_ICONS: Record<string, string> = {
  breakfast: '🌅',
  lunch: '☀️',
  dinner: '🌙',
  snack: '🍎',
  unknown: '🍽️',
}

function formatDate(iso: string | null): string {
  if (!iso) return ''
  try {
    return new Date(iso).toLocaleDateString('fa-IR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    })
  } catch {
    return iso.substring(0, 10)
  }
}

export default function PlanSummary({ plan, dict }: Props) {
  const g = plan.daily_guidelines

  return (
    <div className="space-y-5">
      {/* Summary */}
      {plan.summary && (
        <div className="rounded-2xl bg-elevated p-5 shadow-sm">
          <p className="text-xs font-semibold text-ink-3 uppercase tracking-wide mb-2">
            {dict.plan.summary}
          </p>
          <p className="text-sm text-ink-2 leading-relaxed">{plan.summary}</p>
          <div className="mt-3 flex items-center gap-2 flex-wrap">
            {plan.is_mock && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-muted text-brand font-medium">
                {dict.plan.mockBadge}
              </span>
            )}
            {!plan.is_mock && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-success/10 text-success font-medium">
                {dict.plan.liveBadge}
              </span>
            )}
            {plan.generated_at && (
              <span className="text-xs text-ink-3">
                {dict.plan.generatedAt}: {formatDate(plan.generated_at)}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Daily Guidelines */}
      {g && (
        <div className="rounded-2xl bg-elevated p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-ink mb-4">
            {dict.plan.dailyGuidelinesTitle}
          </h3>
          <div className="grid grid-cols-3 gap-3">
            {g.calories != null && (
              <GuidelineChip
                label={dict.plan.calories}
                value={`${g.calories}`}
                unit={dict.plan.unitKcal}
              />
            )}
            {g.protein_g != null && (
              <GuidelineChip
                label={dict.plan.protein}
                value={`${g.protein_g}`}
                unit={dict.plan.unitGrams}
              />
            )}
            {g.carbs_g != null && (
              <GuidelineChip
                label={dict.plan.carbs}
                value={`${g.carbs_g}`}
                unit={dict.plan.unitGrams}
              />
            )}
            {g.fat_g != null && (
              <GuidelineChip
                label={dict.plan.fat}
                value={`${g.fat_g}`}
                unit={dict.plan.unitGrams}
              />
            )}
            {g.fiber_g != null && (
              <GuidelineChip
                label={dict.plan.fiber}
                value={`${g.fiber_g}`}
                unit={dict.plan.unitGrams}
              />
            )}
            {g.water_liters != null && (
              <GuidelineChip
                label={dict.plan.water}
                value={`${g.water_liters}`}
                unit={dict.plan.unitLiters}
              />
            )}
          </div>
          {g.notes && (
            <p className="mt-4 text-xs text-ink-3 leading-relaxed">{g.notes}</p>
          )}
        </div>
      )}

      {/* Meals */}
      {plan.meals.length > 0 && (
        <div className="rounded-2xl bg-elevated p-5 shadow-sm">
          <h3 className="text-sm font-semibold text-ink mb-4">
            {dict.plan.mealsTitle}
          </h3>
          <div className="space-y-4">
            {plan.meals.map((meal, idx) => {
              const mealTimeLabel =
                dict.plan[meal.meal_time as keyof typeof dict.plan] ??
                dict.plan.unknown
              const icon = MEAL_TIME_ICONS[meal.meal_time] ?? '🍽️'
              return (
                <div
                  key={meal.id ?? idx}
                  className="flex items-start gap-3 pb-4 border-b border-line last:border-0 last:pb-0"
                >
                  <span className="text-xl mt-0.5 shrink-0">{icon}</span>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-brand">
                        {String(mealTimeLabel)}
                      </span>
                      {meal.calories_estimate != null && (
                        <span className="text-xs text-ink-3">
                          {meal.calories_estimate} {dict.plan.unitKcal}
                        </span>
                      )}
                    </div>
                    <p className="text-sm font-semibold text-ink mb-1">
                      {meal.name}
                    </p>
                    {meal.description && (
                      <p className="text-xs text-ink-2 leading-relaxed">
                        {meal.description}
                      </p>
                    )}
                    {meal.notes && (
                      <p className="text-xs text-ink-3 mt-1 italic">
                        {meal.notes}
                      </p>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Warnings */}
      {plan.warnings.length > 0 && (
        <div className="rounded-2xl bg-warm-muted border border-warm/20 p-5">
          <h3 className="text-sm font-semibold text-ink mb-3">
            {dict.plan.warnings}
          </h3>
          <ul className="space-y-2">
            {plan.warnings.map((w, i) => (
              <li key={i} className="text-sm text-ink-2 flex gap-2">
                <span className="text-warm shrink-0 mt-0.5">•</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

function GuidelineChip({
  label,
  value,
  unit,
}: {
  label: string
  value: string
  unit: string
}) {
  return (
    <div className="flex flex-col items-center p-3 rounded-xl bg-surface">
      <span className="text-base font-bold text-ink">{value}</span>
      <span className="text-xs text-ink-3 mt-0.5">{unit}</span>
      <span className="text-xs text-ink-3 text-center mt-1 leading-tight">{label}</span>
    </div>
  )
}
