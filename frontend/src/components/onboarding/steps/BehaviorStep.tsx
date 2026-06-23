'use client'

import { useState } from 'react'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import type { BehaviorRequest } from '@/types/onboarding'
import TagInput from '../TagInput'
import SteppedScale from '@/components/ui/SteppedScale'

interface Props {
  dict: Dictionary['onboarding']
  defaultValues?: Partial<BehaviorFormData>
  isSubmitting: boolean
  apiError: string | null
  onSubmit: (data: BehaviorRequest) => void
  onBack: () => void
}

export interface BehaviorFormData {
  emotional_eating: boolean
  night_eating: boolean
  meal_skipping: boolean
  binge_history: boolean
  cravings: string[]
  diet_history: string
  previous_failures: string
  hunger_patterns: string[]
  motivation_level: number
}

const PRESET_CRAVINGS: Array<{ value: string; labelKey: keyof Dictionary['onboarding'] }> = [
  { value: 'sweet', labelKey: 'behavCravSweet' },
  { value: 'salty', labelKey: 'behavCravSalty' },
  { value: 'fried', labelKey: 'behavCravFried' },
  { value: 'bread', labelKey: 'behavCravBread' },
  { value: 'chocolate', labelKey: 'behavCravChocolate' },
]

const HUNGER_OPTIONS: Array<{ value: string; labelKey: keyof Dictionary['onboarding'] }> = [
  { value: 'morning', labelKey: 'behavHungerMorning' },
  { value: 'afternoon', labelKey: 'behavHungerAfternoon' },
  { value: 'evening', labelKey: 'behavHungerEvening' },
  { value: 'night', labelKey: 'behavHungerNight' },
  { value: 'random', labelKey: 'behavHungerRandom' },
]

const RANDOM_HUNGER = 'random'

const defaultBehavior: BehaviorFormData = {
  emotional_eating: false,
  night_eating: false,
  meal_skipping: false,
  binge_history: false,
  cravings: [],
  diet_history: '',
  previous_failures: '',
  hunger_patterns: [],
  motivation_level: 7,
}

export default function BehaviorStep({ dict, defaultValues, isSubmitting, apiError, onSubmit }: Props) {
  const [form, setForm] = useState<BehaviorFormData>({ ...defaultBehavior, ...defaultValues })

  function toggleBool(key: keyof Pick<BehaviorFormData, 'emotional_eating' | 'night_eating' | 'meal_skipping' | 'binge_history'>) {
    setForm((f) => ({ ...f, [key]: !f[key] }))
  }

  function toggleCraving(value: string) {
    setForm((f) => ({
      ...f,
      cravings: f.cravings.includes(value)
        ? f.cravings.filter((c) => c !== value)
        : [...f.cravings, value],
    }))
  }

  function toggleHunger(value: string) {
    setForm((f) => {
      if (value === RANDOM_HUNGER) {
        // "no specific pattern" is exclusive
        return { ...f, hunger_patterns: [RANDOM_HUNGER] }
      }
      // selecting a specific option deselects "random"
      const without = f.hunger_patterns.filter((h) => h !== RANDOM_HUNGER && h !== value)
      return {
        ...f,
        hunger_patterns: f.hunger_patterns.includes(value)
          ? without
          : [...without, value],
      }
    })
  }

  function handleSubmit() {
    onSubmit({
      emotional_eating: form.emotional_eating,
      night_eating: form.night_eating,
      meal_skipping: form.meal_skipping,
      binge_history: form.binge_history,
      cravings: form.cravings,
      diet_history: form.diet_history,
      previous_failures: form.previous_failures,
      hunger_patterns: form.hunger_patterns,
      motivation_level: form.motivation_level,
    })
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-2 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-ink">{dict.behavTitle}</h1>
          <p className="text-sm text-ink-2 mt-1">{dict.behavSubtitle}</p>
        </div>

        {/* Boolean behaviors */}
        <div className="rounded-2xl bg-elevated border border-line overflow-hidden">
          {(
            [
              { key: 'emotional_eating', labelKey: 'behavEmotional' },
              { key: 'night_eating', labelKey: 'behavNight' },
              { key: 'meal_skipping', labelKey: 'behavSkipping' },
              { key: 'binge_history', labelKey: 'behavBinge' },
            ] as const
          ).map(({ key, labelKey }, i, arr) => (
            <label
              key={key}
              className={cn(
                'flex items-start justify-between gap-3 px-4 py-3.5 cursor-pointer',
                i < arr.length - 1 && 'border-b border-line',
              )}
            >
              <span className="text-sm text-ink leading-snug flex-1">{dict[labelKey]}</span>
              <Toggle checked={form[key]} onToggle={() => toggleBool(key)} />
            </label>
          ))}
        </div>

        {/* Cravings */}
        <section>
          <p className="text-sm font-semibold text-ink mb-3">{dict.behavCravings}</p>
          <div className="flex flex-wrap gap-2 mb-3">
            {PRESET_CRAVINGS.map(({ value, labelKey }) => (
              <button
                key={value}
                type="button"
                onClick={() => toggleCraving(value)}
                className={cn(
                  'px-3 py-1.5 rounded-full border text-sm transition-colors',
                  form.cravings.includes(value)
                    ? 'border-brand bg-brand-muted text-brand font-medium'
                    : 'border-line bg-elevated text-ink-2',
                )}
              >
                {dict[labelKey]}
              </button>
            ))}
          </div>
          <TagInput
            value={form.cravings.filter((c) => !PRESET_CRAVINGS.some((p) => p.value === c))}
            onChange={(custom) =>
              setForm((f) => ({
                ...f,
                cravings: [
                  ...f.cravings.filter((c) => PRESET_CRAVINGS.some((p) => p.value === c)),
                  ...custom,
                ],
              }))
            }
            placeholder={dict.behavCravOtherPlaceholder}
            addLabel={dict.behavAddCraving}
          />
        </section>

        {/* Hunger pattern — multi-select */}
        <section>
          <p className="text-sm font-semibold text-ink mb-1">{dict.behavHunger}</p>
          <p className="text-xs text-ink-3 mb-3">{dict.behavHungerHint}</p>
          <div className="space-y-2">
            {HUNGER_OPTIONS.map(({ value, labelKey }) => {
              const isActive = form.hunger_patterns.includes(value)
              const isRandom = value === RANDOM_HUNGER
              return (
                <button
                  key={value}
                  type="button"
                  onClick={() => toggleHunger(value)}
                  className={cn(
                    'w-full text-start px-4 py-2.5 rounded-xl border text-sm transition-colors',
                    isActive
                      ? isRandom
                        ? 'border-ink-2 bg-elevated text-ink font-medium'
                        : 'border-brand bg-brand-muted text-brand font-medium'
                      : 'border-line bg-elevated text-ink-2',
                  )}
                >
                  {dict[labelKey]}
                </button>
              )
            })}
          </div>
        </section>

        {/* Motivation */}
        <div>
          <label className="text-sm font-semibold text-ink mb-2 block">{dict.behavMotivation}</label>
          <SteppedScale
            value={form.motivation_level}
            onChange={(v) => setForm((f) => ({ ...f, motivation_level: v }))}
            min={1}
            max={10}
            lowLabel={dict.behavMotivationLow}
            highLabel={dict.behavMotivationHigh}
          />
        </div>

        {/* Diet history */}
        <section>
          <p className="text-sm font-semibold text-ink mb-2">{dict.behavDietHistory}</p>
          <textarea
            value={form.diet_history}
            onChange={(e) => setForm((f) => ({ ...f, diet_history: e.target.value }))}
            placeholder={dict.behavDietHistoryPlaceholder}
            rows={3}
            maxLength={2000}
            className="w-full px-4 py-3 rounded-xl border border-line bg-elevated text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors resize-none"
          />
        </section>

        {/* Previous failures */}
        <section>
          <p className="text-sm font-semibold text-ink mb-2">{dict.behavPreviousFails}</p>
          <textarea
            value={form.previous_failures}
            onChange={(e) => setForm((f) => ({ ...f, previous_failures: e.target.value }))}
            placeholder={dict.behavPreviousFailsPlaceholder}
            rows={3}
            maxLength={2000}
            className="w-full px-4 py-3 rounded-xl border border-line bg-elevated text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors resize-none"
          />
        </section>

        {apiError && (
          <p className="text-sm text-error bg-error/10 rounded-xl px-4 py-3">{apiError}</p>
        )}
      </div>

      <div className="px-6 pb-safe pb-8 pt-4 border-t border-line shrink-0">
        <button
          type="button"
          onClick={handleSubmit}
          disabled={isSubmitting}
          className="w-full py-3.5 rounded-2xl bg-brand text-white font-semibold text-base disabled:opacity-60 transition-opacity"
        >
          {isSubmitting ? dict.saving : dict.next}
        </button>
      </div>
    </div>
  )
}

function Toggle({ checked, onToggle }: { checked: boolean; onToggle: () => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={onToggle}
      className={cn(
        'relative w-11 h-6 rounded-full transition-colors duration-200 shrink-0',
        checked ? 'bg-brand' : 'bg-line',
      )}
    >
      <span
        className={cn(
          'absolute top-0.5 h-5 w-5 rounded-full bg-white shadow-sm transition-transform duration-200',
          checked ? 'translate-x-5' : 'translate-x-0.5',
        )}
      />
    </button>
  )
}
