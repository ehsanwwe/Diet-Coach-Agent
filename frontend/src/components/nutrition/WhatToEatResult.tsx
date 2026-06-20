import type { FoodOption, WhatToEatNowResponse } from '@/types/nutrition'
import type { Dictionary } from '@/dictionaries/fa'

interface Props {
  result: WhatToEatNowResponse
  dict: Pick<Dictionary, 'whatToEat' | 'plan'>
  onReset: () => void
}

function optionLabel(dict: Props['dict'], type?: FoodOption['option_type'] | null): string | null {
  if (type === 'best_goal_aligned') return dict.whatToEat.bestAligned
  if (type === 'fastest') return dict.whatToEat.fastest
  if (type === 'flexible') return dict.whatToEat.flexible
  return null
}

function OptionCard({
  opt,
  dict,
  badge,
  showMock,
}: {
  opt: FoodOption
  dict: Props['dict']
  badge?: string | null
  showMock?: boolean
}) {
  const label = badge ?? optionLabel(dict, opt.option_type)

  return (
    <div className="rounded-2xl bg-elevated p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3 mb-2">
        <h3 className="text-base font-semibold text-ink">{opt.name}</h3>
        <div className="flex flex-col items-end gap-1 shrink-0">
          {label && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-brand-muted text-brand font-medium">
              {label}
            </span>
          )}
          {showMock && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-surface text-ink-3 font-medium">
              {dict.whatToEat.mockBadge}
            </span>
          )}
        </div>
      </div>
      {opt.description && (
        <p className="text-sm text-ink-2 leading-relaxed mb-3">{opt.description}</p>
      )}
      <div className="flex flex-wrap items-center gap-3 text-xs text-ink-3">
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
      {opt.household_portions && (
        <p className="text-sm text-ink-2 mt-3">
          <span className="font-semibold text-brand">{dict.whatToEat.householdPortions}: </span>
          {opt.household_portions}
        </p>
      )}
      {opt.why_it_fits_goal && (
        <p className="text-sm text-ink-2 mt-2">
          <span className="font-semibold text-brand">{dict.whatToEat.whyFitsGoal}: </span>
          {opt.why_it_fits_goal}
        </p>
      )}
      {(opt.substitutions?.length ?? 0) > 0 && (
        <div className="flex flex-wrap gap-2 mt-3">
          {opt.substitutions?.map((sub) => (
            <span key={sub} className="text-xs px-2.5 py-1 rounded-full bg-brand-muted text-brand">
              {sub}
            </span>
          ))}
        </div>
      )}
      {opt.safety_note && (
        <p className="text-xs text-warm bg-warm-muted rounded-xl px-3 py-2 mt-3">
          {dict.whatToEat.safetyNote}: {opt.safety_note}
        </p>
      )}
    </div>
  )
}

export default function WhatToEatResult({ result, dict, onReset }: Props) {
  const highlighted = [
    { opt: result.best_goal_aligned_option, badge: dict.whatToEat.bestAligned },
    { opt: result.fastest_option, badge: dict.whatToEat.fastest },
    { opt: result.flexible_option, badge: dict.whatToEat.flexible },
  ].filter((item): item is { opt: FoodOption; badge: string } => Boolean(item.opt))

  const highlightedNames = new Set(highlighted.map((item) => item.opt.name))
  const otherOptions = result.options.filter((opt) => !highlightedNames.has(opt.name))

  return (
    <div className="space-y-5">
      <div className="space-y-4">
        <h2 className="text-sm font-semibold text-ink">{dict.whatToEat.optionsTitle}</h2>
        {(highlighted.length > 0 ? highlighted : result.options.map((opt) => ({ opt, badge: optionLabel(dict, opt.option_type) ?? undefined }))).map((item, i) => (
          <OptionCard
            key={`${item.badge ?? 'option'}-${item.opt.name}-${i}`}
            opt={item.opt}
            dict={dict}
            badge={item.badge}
            showMock={result.is_mock && i === 0}
          />
        ))}
        {otherOptions.map((opt, i) => (
          <OptionCard key={`${opt.name}-${i}`} opt={opt} dict={dict} />
        ))}
      </div>

      {result.reasoning_summary && (
        <div className="rounded-2xl bg-surface p-5">
          <h3 className="text-sm font-semibold text-ink mb-2">
            {dict.whatToEat.reasoningTitle}
          </h3>
          <p className="text-sm text-ink-2 leading-relaxed">{result.reasoning_summary}</p>
        </div>
      )}

      {(result.warnings?.length ?? 0) > 0 && (
        <div className="rounded-2xl bg-warm-muted border border-warm/20 p-5">
          <h3 className="text-sm font-semibold text-ink mb-3">
            {dict.whatToEat.warningsTitle}
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
        {dict.whatToEat.tryAgainBtn}
      </button>
    </div>
  )
}
