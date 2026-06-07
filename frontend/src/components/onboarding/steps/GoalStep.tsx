'use client'

import { useState } from 'react'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import { ALL_GOALS, type GoalType } from '@/types/onboarding'
import AppIcon, { type AppIconName } from '@/components/ui/AppIcon'

interface Props {
  dict: Dictionary['onboarding']
  defaultValue: GoalType | null
  onSubmit: (goal: GoalType) => void
  onBack: () => void
}

const GOAL_LABEL_KEYS: Record<GoalType, keyof Dictionary['onboarding']> = {
  weight_loss: 'goalWeightLoss',
  weight_gain: 'goalWeightGain',
  muscle_gain: 'goalMuscleGain',
  healthy_eating: 'goalHealthyEating',
  diabetes_support: 'goalDiabetes',
  fatty_liver_support: 'goalFattyLiver',
  pcos_support: 'goalPcos',
  digestive_support: 'goalDigestive',
  sports_nutrition: 'goalSports',
  pregnancy_breastfeeding_caution: 'goalPregnancy',
  general_health_companion: 'goalGeneral',
}

const GOAL_ICONS: Record<GoalType, AppIconName> = {
  weight_loss: 'weight',
  weight_gain: 'progress',
  muscle_gain: 'muscle',
  healthy_eating: 'healthyEating',
  diabetes_support: 'medical',
  fatty_liver_support: 'safety',
  pcos_support: 'pcos',
  digestive_support: 'digestive',
  sports_nutrition: 'sports',
  pregnancy_breastfeeding_caution: 'baby',
  general_health_companion: 'generalHealth',
}

export default function GoalStep({ dict, defaultValue, onSubmit }: Props) {
  const [selected, setSelected] = useState<GoalType | null>(defaultValue)
  const [touched, setTouched] = useState(false)

  function handleNext() {
    setTouched(true)
    if (selected) onSubmit(selected)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-2">
        <div className="mb-4">
          <h1 className="text-xl font-bold text-ink">{dict.goalTitle}</h1>
          <p className="text-sm text-ink-2 mt-1">{dict.goalSubtitle}</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {ALL_GOALS.map((goal) => (
            <button
              key={goal}
              type="button"
              onClick={() => setSelected(goal)}
              className={cn(
                'flex flex-col items-center gap-2 p-4 rounded-2xl border text-center transition-all',
                selected === goal
                  ? 'border-brand bg-brand-muted shadow-sm'
                  : 'border-line bg-elevated hover:border-brand-light',
              )}
            >
              <AppIcon
                name={GOAL_ICONS[goal]}
                className={selected === goal ? 'text-brand' : 'text-ink-2'}
                size={24}
              />
              <span
                className={cn(
                  'text-xs font-medium leading-snug',
                  selected === goal ? 'text-brand' : 'text-ink',
                )}
              >
                {dict[GOAL_LABEL_KEYS[goal]] as string}
              </span>
            </button>
          ))}
        </div>

        {touched && !selected && (
          <p className="text-xs text-error mt-3">{dict.goalSelectPrompt}</p>
        )}
      </div>

      <div className="px-6 pb-safe pb-8 pt-4 border-t border-line">
        <button
          type="button"
          onClick={handleNext}
          className="w-full py-3.5 rounded-2xl bg-brand text-white font-semibold text-base transition-opacity disabled:opacity-60"
        >
          {dict.next}
        </button>
      </div>
    </div>
  )
}
