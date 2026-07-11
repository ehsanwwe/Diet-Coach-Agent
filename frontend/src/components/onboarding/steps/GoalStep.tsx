'use client'

import { useMemo, useState } from 'react'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import {
  ALL_GOALS,
  filterGoalsForGender,
  type Gender,
  type GoalType,
} from '@/types/onboarding'
import AppIcon, { type AppIconName } from '@/components/ui/AppIcon'

interface Props {
  dict: Dictionary['onboarding']
  defaultValue: GoalType[]
  gender: Gender | null | undefined
  isSubmitting: boolean
  apiError: string | null
  onSubmit: (goals: GoalType[]) => void
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

export default function GoalStep({ dict, defaultValue, gender, isSubmitting, apiError, onSubmit }: Props) {
  const visibleGoals = useMemo(() => filterGoalsForGender(ALL_GOALS, gender), [gender])
  const [selected, setSelected] = useState<GoalType[]>(() =>
    filterGoalsForGender(defaultValue, gender),
  )
  const [touched, setTouched] = useState(false)

  function toggleGoal(goal: GoalType) {
    setSelected((prev) =>
      prev.includes(goal) ? prev.filter((g) => g !== goal) : [...prev, goal],
    )
  }

  function handleNext() {
    setTouched(true)
    const sanitized = filterGoalsForGender(selected, gender)
    if (sanitized.length > 0) onSubmit(sanitized)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto min-h-0 px-6 py-2">
        <div className="mb-4">
          <h1 className="text-xl font-bold text-ink">{dict.goalTitle}</h1>
          <p className="text-sm text-ink-2 mt-1">{dict.goalSubtitle}</p>
        </div>

        <div className="grid grid-cols-2 gap-3">
          {visibleGoals.map((goal) => {
            const isActive = selected.includes(goal)
            return (
              <button
                key={goal}
                type="button"
                onClick={() => toggleGoal(goal)}
                className={cn(
                  'flex flex-col items-center gap-2 p-4 rounded-2xl border text-center transition-all',
                  isActive
                    ? 'border-brand bg-brand-muted shadow-sm'
                    : 'border-line bg-elevated hover:border-brand-light',
                )}
              >
                <AppIcon
                  name={GOAL_ICONS[goal]}
                  className={isActive ? 'text-brand' : 'text-ink-2'}
                  size={24}
                />
                <span
                  className={cn(
                    'text-xs font-medium leading-snug',
                    isActive ? 'text-brand' : 'text-ink',
                  )}
                >
                  {dict[GOAL_LABEL_KEYS[goal]] as string}
                </span>
              </button>
            )
          })}
        </div>

        {touched && selected.length === 0 && (
          <p className="text-xs text-error mt-3">{dict.goalSelectPrompt}</p>
        )}

        {apiError && (
          <p className="text-sm text-error bg-error/10 rounded-xl px-4 py-3 mt-3">{apiError}</p>
        )}
      </div>

      <div className="px-6 pb-safe pb-8 pt-4 border-t border-line">
        <button
          type="button"
          onClick={handleNext}
          disabled={isSubmitting}
          className="w-full py-3.5 rounded-2xl bg-brand text-white font-semibold text-base transition-opacity disabled:opacity-60"
        >
          {isSubmitting ? dict.saving : dict.next}
        </button>
      </div>
    </div>
  )
}
