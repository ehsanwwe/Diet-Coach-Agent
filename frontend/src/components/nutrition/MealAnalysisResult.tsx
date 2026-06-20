import type { MealAnalysisResponse } from '@/types/nutrition'
import type { Dictionary } from '@/dictionaries/fa'
import AppIcon from '@/components/ui/AppIcon'

interface Props {
  result: MealAnalysisResponse
  dict: Pick<Dictionary, 'mealAnalysis' | 'common'>
  onReset: () => void
}

function DetailRows({ rows }: { rows: { label: string; value?: string | null }[] }) {
  const visible = rows.filter((row) => row.value)
  if (visible.length === 0) return null

  return (
    <div className="rounded-2xl bg-elevated p-5 shadow-sm space-y-3">
      {visible.map((row) => (
        <div key={row.label}>
          <span className="text-xs font-semibold text-brand">{row.label}</span>
          <p className="text-sm text-ink-2 mt-0.5 leading-relaxed">{row.value}</p>
        </div>
      ))}
    </div>
  )
}

export default function MealAnalysisResult({ result, dict, onReset }: Props) {
  const scoreColor =
    (result.quality_score ?? 0) >= 8
      ? 'text-success'
      : (result.quality_score ?? 0) >= 5
      ? 'text-brand'
      : 'text-warm'

  return (
    <div className="space-y-5">
      {result.quality_score != null && (
        <div className="rounded-2xl bg-elevated p-5 shadow-sm flex items-center gap-4">
          <div className={`text-4xl font-bold ${scoreColor}`}>
            {result.quality_score}
          </div>
          <div>
            <p className="text-sm font-medium text-ink">{dict.mealAnalysis.qualityScore}</p>
            <p className="text-xs text-ink-3">{dict.mealAnalysis.outOf10}</p>
          </div>
          <div className="ms-auto">
            {result.is_mock && (
              <span className="text-xs px-2 py-0.5 rounded-full bg-brand-muted text-brand font-medium">
                {dict.mealAnalysis.mockBadge}
              </span>
            )}
          </div>
        </div>
      )}

      <div className="rounded-2xl bg-elevated p-5 shadow-sm">
        <p className="text-sm text-ink-2 leading-relaxed">{result.analysis_summary}</p>
      </div>

      <DetailRows
        rows={[
          { label: dict.mealAnalysis.likelyMeal, value: result.likely_meal },
          { label: dict.mealAnalysis.goalEffect, value: result.likely_goal_effect },
        ]}
      />

      {(result.uncertainties?.length ?? 0) > 0 && (
        <div className="rounded-2xl bg-surface p-5">
          <h3 className="text-sm font-semibold text-ink mb-3">
            {dict.mealAnalysis.uncertainties}
          </h3>
          <ul className="space-y-2">
            {result.uncertainties?.map((item, i) => (
              <li key={i} className="text-sm text-ink-2 flex gap-2">
                <span className="text-ink-3 shrink-0">-</span>
                {item}
              </li>
            ))}
          </ul>
        </div>
      )}

      <DetailRows
        rows={[
          { label: dict.mealAnalysis.protein, value: result.protein },
          { label: dict.mealAnalysis.fiber, value: result.fiber },
          { label: dict.mealAnalysis.sugar, value: result.sugar },
          { label: dict.mealAnalysis.balance, value: result.balance },
          { label: dict.mealAnalysis.portion, value: result.portion },
        ]}
      />

      <div className="space-y-3">
        <h3 className="text-sm font-semibold text-ink">
          {dict.mealAnalysis.nutritionQualityTitle}
        </h3>
        <DetailRows
          rows={[
            { label: dict.mealAnalysis.proteinQuality, value: result.protein_quality },
            { label: dict.mealAnalysis.fiberVegetableQuality, value: result.fiber_vegetable_quality },
            { label: dict.mealAnalysis.carbohydrateQuality, value: result.carbohydrate_quality },
            { label: dict.mealAnalysis.fatQuality, value: result.fat_quality },
            { label: dict.mealAnalysis.simpleSugarQuality, value: result.simple_sugar_quality },
            { label: dict.mealAnalysis.portionVolumeAssessment, value: result.portion_volume_assessment },
            { label: dict.mealAnalysis.satietyAssessment, value: result.satiety_assessment },
          ]}
        />
      </div>

      <DetailRows
        rows={[
          { label: dict.mealAnalysis.smallCorrection, value: result.one_small_correction },
          { label: dict.mealAnalysis.nextMealSuggestion, value: result.next_meal_suggestion },
          { label: dict.mealAnalysis.noExtremeCompensation, value: result.no_extreme_compensation_note },
        ]}
      />

      {(result.suggestions?.length ?? 0) > 0 && (
        <div className="rounded-2xl bg-brand-muted p-5">
          <h3 className="text-sm font-semibold text-ink mb-3">
            {dict.mealAnalysis.suggestionsTitle}
          </h3>
          <ul className="space-y-2">
            {result.suggestions?.map((s, i) => (
              <li key={i} className="text-sm text-ink-2 flex gap-2">
                <AppIcon name="check" className="text-brand shrink-0 mt-0.5" size={15} />
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {(result.warnings?.length ?? 0) > 0 && (
        <div className="rounded-2xl bg-warm-muted border border-warm/20 p-5">
          <h3 className="text-sm font-semibold text-ink mb-3">
            {dict.mealAnalysis.warningsTitle}
          </h3>
          <ul className="space-y-2">
            {result.warnings?.map((w, i) => (
              <li key={i} className="text-sm text-ink-2 flex gap-2">
                <span className="text-warm shrink-0">-</span>
                {w}
              </li>
            ))}
          </ul>
        </div>
      )}

      <button
        onClick={onReset}
        className="w-full py-4 rounded-2xl border border-brand text-brand font-semibold text-sm"
      >
        {dict.mealAnalysis.newAnalysisBtn}
      </button>
    </div>
  )
}
