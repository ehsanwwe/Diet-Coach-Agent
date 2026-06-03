'use client'

import { useState } from 'react'
import { cn } from '@/lib/cn'
import type { Dictionary } from '@/dictionaries/fa'
import type { PreferencesRequest } from '@/types/onboarding'
import TagInput from '../TagInput'

interface Props {
  dict: Dictionary['onboarding']
  defaultValues?: Partial<PreferencesFormData>
  isSubmitting: boolean
  apiError: string | null
  onSubmit: (data: PreferencesRequest) => void
  onBack: () => void
}

export interface PreferencesFormData {
  likes_iranian_food: boolean
  vegetarian: boolean
  vegan: boolean
  halal: boolean
  disliked_foods: string[]
  favorite_foods: string[]
  breakfast_habit: string
  rice_frequency: string
  bread_frequency: string
  sweets_frequency: string
  tea_frequency: string
  restaurant_frequency: string
}

const defaultPrefs: PreferencesFormData = {
  likes_iranian_food: true,
  vegetarian: false,
  vegan: false,
  halal: true,
  disliked_foods: [],
  favorite_foods: [],
  breakfast_habit: 'light',
  rice_frequency: 'daily',
  bread_frequency: 'daily',
  sweets_frequency: 'rarely',
  tea_frequency: 'few_weekly',
  restaurant_frequency: 'rarely',
}

const FREQ_OPTIONS: Array<{ value: string; labelKey: keyof Dictionary['onboarding'] }> = [
  { value: 'never', labelKey: 'consumNever' },
  { value: 'rarely', labelKey: 'consumRarely' },
  { value: 'few_weekly', labelKey: 'consumFewWeekly' },
  { value: 'daily', labelKey: 'consumDaily' },
  { value: 'several_daily', labelKey: 'consumSeveralDaily' },
]

const BREAKFAST_OPTIONS: Array<{ value: string; labelKey: keyof Dictionary['onboarding'] }> = [
  { value: 'skip', labelKey: 'prefBreakfastSkip' },
  { value: 'light', labelKey: 'prefBreakfastLight' },
  { value: 'full', labelKey: 'prefBreakfastFull' },
  { value: 'varies', labelKey: 'prefBreakfastVaries' },
]

export default function PreferencesStep({ dict, defaultValues, isSubmitting, apiError, onSubmit }: Props) {
  const [form, setForm] = useState<PreferencesFormData>({ ...defaultPrefs, ...defaultValues })

  function toggle(key: keyof Pick<PreferencesFormData, 'likes_iranian_food' | 'vegetarian' | 'vegan' | 'halal'>) {
    setForm((f) => ({ ...f, [key]: !f[key] }))
  }

  function setField(key: keyof PreferencesFormData, value: string) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  function handleSubmit() {
    onSubmit(form)
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto px-6 py-2 space-y-6">
        <div>
          <h1 className="text-xl font-bold text-ink">{dict.prefTitle}</h1>
          <p className="text-sm text-ink-2 mt-1">{dict.prefSubtitle}</p>
        </div>

        {/* Toggle preferences */}
        <div className="rounded-2xl bg-elevated border border-line overflow-hidden">
          {(
            [
              { key: 'likes_iranian_food', labelKey: 'prefIranianFood' },
              { key: 'vegetarian', labelKey: 'prefVegetarian' },
              { key: 'vegan', labelKey: 'prefVegan' },
              { key: 'halal', labelKey: 'prefHalal' },
            ] as const
          ).map(({ key, labelKey }, i, arr) => (
            <label
              key={key}
              className={cn(
                'flex items-center justify-between px-4 py-3.5 cursor-pointer',
                i < arr.length - 1 && 'border-b border-line',
              )}
            >
              <span className="text-sm text-ink">{dict[labelKey]}</span>
              <Toggle checked={form[key]} onToggle={() => toggle(key)} />
            </label>
          ))}
        </div>

        {/* Disliked foods */}
        <section>
          <p className="text-sm font-semibold text-ink mb-2">{dict.prefDisliked}</p>
          <TagInput
            value={form.disliked_foods}
            onChange={(v) => setForm((f) => ({ ...f, disliked_foods: v }))}
            placeholder={dict.prefDislikedPlaceholder}
            addLabel={dict.prefAddFood}
          />
        </section>

        {/* Favourite foods */}
        <section>
          <p className="text-sm font-semibold text-ink mb-2">{dict.prefFavorite}</p>
          <TagInput
            value={form.favorite_foods}
            onChange={(v) => setForm((f) => ({ ...f, favorite_foods: v }))}
            placeholder={dict.prefFavoritePlaceholder}
            addLabel={dict.prefAddFood}
          />
        </section>

        {/* Breakfast habit */}
        <section>
          <p className="text-sm font-semibold text-ink mb-2">{dict.prefBreakfast}</p>
          <div className="grid grid-cols-2 gap-2">
            {BREAKFAST_OPTIONS.map(({ value, labelKey }) => (
              <button
                key={value}
                type="button"
                onClick={() => setField('breakfast_habit', value)}
                className={cn(
                  'py-2.5 px-3 rounded-xl border text-sm transition-colors',
                  form.breakfast_habit === value
                    ? 'border-brand bg-brand-muted text-brand font-medium'
                    : 'border-line bg-elevated text-ink-2',
                )}
              >
                {dict[labelKey]}
              </button>
            ))}
          </div>
        </section>

        {/* Consumption frequencies */}
        {(
          [
            { field: 'rice_frequency', labelKey: 'prefRice' },
            { field: 'bread_frequency', labelKey: 'prefBread' },
            { field: 'sweets_frequency', labelKey: 'prefSweets' },
            { field: 'tea_frequency', labelKey: 'prefTea' },
            { field: 'restaurant_frequency', labelKey: 'prefRestaurant' },
          ] as const
        ).map(({ field, labelKey }) => (
          <section key={field}>
            <p className="text-sm font-semibold text-ink mb-2">{dict[labelKey]}</p>
            <div className="flex gap-1.5 flex-wrap">
              {FREQ_OPTIONS.map(({ value, labelKey: flk }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setField(field, value)}
                  className={cn(
                    'px-3 py-1.5 rounded-full border text-xs transition-colors',
                    form[field] === value
                      ? 'border-brand bg-brand-muted text-brand font-medium'
                      : 'border-line bg-elevated text-ink-3',
                  )}
                >
                  {dict[flk]}
                </button>
              ))}
            </div>
          </section>
        ))}

        {apiError && (
          <p className="text-sm text-error bg-error/10 rounded-xl px-4 py-3">{apiError}</p>
        )}
      </div>

      <div className="px-6 pb-safe pb-8 pt-4 border-t border-line">
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
