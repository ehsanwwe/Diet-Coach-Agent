import type { MealAnalysisResponse } from '@/types/nutrition'
import type { Dictionary } from '@/dictionaries/fa'

interface Props {
  result: MealAnalysisResponse
  dict: Pick<Dictionary, 'mealAnalysis' | 'common'>
  onReset: () => void
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
      {/* Score */}
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

      {/* Summary */}
      <div className="rounded-2xl bg-elevated p-5 shadow-sm">
        <p className="text-sm text-ink-2 leading-relaxed">{result.analysis_summary}</p>
      </div>

      {/* Nutrient details */}
      <div className="rounded-2xl bg-elevated p-5 shadow-sm space-y-3">
        {[
          { label: dict.mealAnalysis.protein, value: result.protein },
          { label: dict.mealAnalysis.fiber, value: result.fiber },
          { label: dict.mealAnalysis.sugar, value: result.sugar },
          { label: dict.mealAnalysis.balance, value: result.balance },
          { label: dict.mealAnalysis.portion, value: result.portion },
        ]
          .filter((r) => r.value)
          .map((row) => (
            <div key={row.label}>
              <span className="text-xs font-semibold text-brand">{row.label}</span>
              <p className="text-sm text-ink-2 mt-0.5">{row.value}</p>
            </div>
          ))}
      </div>

      {/* Suggestions */}
      {result.suggestions.length > 0 && (
        <div className="rounded-2xl bg-brand-muted p-5">
          <h3 className="text-sm font-semibold text-ink mb-3">
            {dict.mealAnalysis.suggestionsTitle}
          </h3>
          <ul className="space-y-2">
            {result.suggestions.map((s, i) => (
              <li key={i} className="text-sm text-ink-2 flex gap-2">
                <span className="text-brand shrink-0">✓</span>
                {s}
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div className="rounded-2xl bg-warm-muted border border-warm/20 p-5">
          <h3 className="text-sm font-semibold text-ink mb-3">
            {dict.mealAnalysis.warningsTitle}
          </h3>
          <ul className="space-y-2">
            {result.warnings.map((w, i) => (
              <li key={i} className="text-sm text-ink-2 flex gap-2">
                <span className="text-warm shrink-0">•</span>
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
