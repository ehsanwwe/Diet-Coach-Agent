'use client'

import { forwardRef } from 'react'
import { useForm } from 'react-hook-form'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import type { LifestyleRequest } from '@/types/onboarding'
import SteppedRangeSlider from '@/components/ui/SteppedRangeSlider'

interface Props {
  dict: Dictionary['onboarding']
  defaultValues?: Partial<LifestyleFormData>
  isSubmitting: boolean
  apiError: string | null
  onSubmit: (data: LifestyleRequest) => void
  onBack: () => void
}

export interface LifestyleFormData {
  sleep_hours: number
  stress_level: number
  work_schedule: string
  activity_level: string
  exercise_days_per_week: number
  cooking_ability: number
  food_budget: string
  travel_frequency: string
}

export default function LifestyleStep({ dict, defaultValues, isSubmitting, apiError, onSubmit }: Props) {
  const { register, handleSubmit, watch, setValue, formState: { errors } } = useForm<LifestyleFormData>({
    defaultValues: {
      sleep_hours: defaultValues?.sleep_hours ?? 7,
      stress_level: defaultValues?.stress_level ?? 5,
      work_schedule: defaultValues?.work_schedule ?? '',
      activity_level: defaultValues?.activity_level ?? '',
      exercise_days_per_week: defaultValues?.exercise_days_per_week ?? 3,
      cooking_ability: defaultValues?.cooking_ability ?? 3,
      food_budget: defaultValues?.food_budget ?? '',
      travel_frequency: defaultValues?.travel_frequency ?? '',
    },
  })

  const sleepVal = watch('sleep_hours')
  const stressVal = watch('stress_level')
  const cookingVal = watch('cooking_ability')
  const exerciseVal = watch('exercise_days_per_week')

  return (
    <form onSubmit={handleSubmit((d) => onSubmit(d))} className="h-full min-h-0 flex flex-col">
      <div className="flex-1 overflow-y-auto min-h-0 px-6 py-2 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-ink">{dict.lifestyleTitle}</h1>
          <p className="text-sm text-ink-2 mt-1">{dict.lifestyleSubtitle}</p>
        </div>

        {/* Sleep */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-ink-2">{dict.lifeSleep}</label>
            <span className="text-sm font-semibold text-brand">{sleepVal} {dict.lifeSleepUnit}</span>
          </div>
          <SteppedRangeSlider
            value={Math.min(12, Math.max(3, sleepVal))}
            onChange={(v) => setValue('sleep_hours', v)}
            min={3}
            max={12}
            step={1}
            lowLabel="3"
            highLabel="12"
          />
        </div>

        {/* Stress */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-ink-2">{dict.lifeStress}</label>
            <span className="text-sm font-semibold text-brand">{stressVal} {dict.outOf10}</span>
          </div>
          <SteppedRangeSlider
            value={stressVal}
            onChange={(v) => setValue('stress_level', v)}
            min={1}
            max={10}
            lowLabel={dict.lifeStressLow}
            highLabel={dict.lifeStressHigh}
          />
        </div>

        {/* Work schedule */}
        <SelectField label={dict.lifeWork} error={errors.work_schedule && dict.lifeRequired}
          {...register('work_schedule', { required: true })}>
          <option value="">{dict.lifeRequired}</option>
          <option value="regular">{dict.lifeWorkRegular}</option>
          <option value="shift">{dict.lifeWorkShift}</option>
          <option value="freelance">{dict.lifeWorkFreelance}</option>
          <option value="student">{dict.lifeWorkStudent}</option>
          <option value="homemaker">{dict.lifeWorkHomemaker}</option>
          <option value="retired">{dict.lifeWorkRetired}</option>
          <option value="other">{dict.lifeWorkOther}</option>
        </SelectField>

        {/* Activity level */}
        <SelectField label={dict.lifeActivity} error={errors.activity_level && dict.lifeRequired}
          {...register('activity_level', { required: true })}>
          <option value="">{dict.lifeRequired}</option>
          <option value="sedentary">{dict.lifeActSedentary}</option>
          <option value="light">{dict.lifeActLight}</option>
          <option value="moderate">{dict.lifeActModerate}</option>
          <option value="active">{dict.lifeActActive}</option>
          <option value="very_active">{dict.lifeActVeryActive}</option>
        </SelectField>

        {/* Exercise days */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-ink-2">{dict.lifeExercise}</label>
            <span className="text-sm font-semibold text-brand">{exerciseVal} {dict.daysUnit}</span>
          </div>
          <SteppedRangeSlider
            value={exerciseVal}
            onChange={(v) => setValue('exercise_days_per_week', v)}
            min={0}
            max={7}
            lowLabel="0"
            highLabel={`7 ${dict.lifeExerciseUnit}`}
          />
        </div>

        {/* Cooking ability */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <label className="text-sm font-medium text-ink-2">{dict.lifeCooking}</label>
            <span className="text-sm font-semibold text-brand">{cookingVal}/5</span>
          </div>
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((v) => (
              <button key={v} type="button" onClick={() => setValue('cooking_ability', v)}
                className={cn('flex-1 py-2 rounded-xl border text-sm font-medium transition-colors',
                  cookingVal >= v ? 'bg-brand border-brand text-white' : 'bg-elevated border-line text-ink-3')}>
                {v}
              </button>
            ))}
          </div>
          <div className="flex justify-between mt-1">
            <span className="text-xs text-ink-3">{dict.lifeCookingLow}</span>
            <span className="text-xs text-ink-3">{dict.lifeCookingHigh}</span>
          </div>
        </div>

        {/* Budget */}
        <SelectField label={dict.lifeBudget} error={errors.food_budget && dict.lifeRequired}
          {...register('food_budget', { required: true })}>
          <option value="">{dict.lifeRequired}</option>
          <option value="low">{dict.lifeBudgetLow}</option>
          <option value="medium">{dict.lifeBudgetMedium}</option>
          <option value="high">{dict.lifeBudgetHigh}</option>
        </SelectField>

        {/* Travel */}
        <SelectField label={dict.lifeTravel} error={errors.travel_frequency && dict.lifeRequired}
          {...register('travel_frequency', { required: true })}>
          <option value="">{dict.lifeRequired}</option>
          <option value="never">{dict.freqNever}</option>
          <option value="rarely">{dict.freqRarely}</option>
          <option value="few_weekly">{dict.freqFewWeekly}</option>
          <option value="daily">{dict.freqDaily}</option>
        </SelectField>

        {apiError && <p className="text-sm text-error bg-error/10 rounded-xl px-4 py-3">{apiError}</p>}
      </div>

      <div className="px-6 pb-safe pb-8 pt-4 border-t border-line shrink-0">
        <button type="submit" disabled={isSubmitting}
          className="w-full py-3.5 rounded-2xl bg-brand text-white font-semibold text-base disabled:opacity-60 transition-opacity">
          {isSubmitting ? dict.saving : dict.next}
        </button>
      </div>
    </form>
  )
}

const SelectField = forwardRef<
  HTMLSelectElement,
  { label: string; error?: string | false; children: React.ReactNode } & React.SelectHTMLAttributes<HTMLSelectElement>
>(function SelectField({ label, error, children, ...props }, ref) {
  return (
    <div>
      <label className="text-sm font-medium text-ink-2 mb-1.5 block">{label}</label>
      <select ref={ref} {...props}
        className={cn('w-full px-4 py-3 rounded-xl border bg-elevated text-ink text-sm focus:outline-none focus:border-brand transition-colors appearance-none',
          error ? 'border-error' : 'border-line')}>
        {children}
      </select>
      {error && <p className="text-xs text-error mt-1.5">{error}</p>}
    </div>
  )
})
