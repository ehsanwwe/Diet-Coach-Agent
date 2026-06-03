import type { WhatToEatNowResponse } from '@/types/nutrition'
import type { Dictionary } from '@/dictionaries/fa'

interface Props {
  result: WhatToEatNowResponse
  dict: Pick<Dictionary, 'whatToEat' | 'plan'>
  onReset: () => void
}

export default function WhatToEatResult({ result, dict, onReset }: Props) {
  return (
    <div className="space-y-5">
      {/* Options */}
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-ink">{dict.whatToEat.optionsTitle}</h2>
        {result.options.map((opt, i) => (
          <div
            key={i}
            className="rounded-2xl bg-elevated p-5 shadow-sm"
          >
            <div className="flex items-start justify-between gap-3 mb-2">
              <h3 className="text-base font-semibold text-ink">{opt.name}</h3>
              {result.is_mock && i === 0 && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-brand-muted text-brand font-medium shrink-0">
                  {dict.whatToEat.mockBadge}
                </span>
              )}
            </div>
            {opt.description && (
              <p className="text-sm text-ink-2 leading-relaxed mb-3">{opt.description}</p>
            )}
            <div className="flex items-center gap-4 text-xs text-ink-3">
              {opt.calories_estimate != null && (
                <span>
                  {dict.whatToEat.calories}: {opt.calories_estimate} {dict.plan.unitKcal}
                </span>
              )}
              {opt.prep_time_minutes != null && (
                <span>
                  {dict.whatToEat.prepTime}: {opt.prep_time_minutes} {dict.plan.unitMin}
                </span>
              )}
            </div>
            {opt.tags.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {opt.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2.5 py-1 rounded-full bg-brand-muted text-brand"
                  >
                    {tag}
                  </span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Reasoning */}
      {result.reasoning_summary && (
        <div className="rounded-2xl bg-surface p-5">
          <h3 className="text-sm font-semibold text-ink mb-2">
            {dict.whatToEat.reasoningTitle}
          </h3>
          <p className="text-sm text-ink-2 leading-relaxed">{result.reasoning_summary}</p>
        </div>
      )}

      {/* Warnings */}
      {result.warnings.length > 0 && (
        <div className="rounded-2xl bg-warm-muted border border-warm/20 p-5">
          <h3 className="text-sm font-semibold text-ink mb-3">
            {dict.whatToEat.warningsTitle}
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
        {dict.whatToEat.tryAgainBtn}
      </button>
    </div>
  )
}
