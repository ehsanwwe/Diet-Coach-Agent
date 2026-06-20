'use client'

import { useState, useRef } from 'react'
import { useRouter } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import type { WhatToEatNowResponse } from '@/types/nutrition'
import { whatToEatNow } from '@/lib/nutrition'
import { ApiRequestError } from '@/lib/api'

type HungerLevel = 'low' | 'medium' | 'high'

interface Props {
  dict: Pick<Dictionary, 'whatToEat' | 'common' | 'errors'>
  locale: Locale
  onResult: (result: WhatToEatNowResponse) => void
}

export default function WhatToEatForm({ dict, locale, onResult }: Props) {
  const router = useRouter()
  const [foods, setFoods] = useState<string[]>([])
  const [inputFood, setInputFood] = useState('')
  const [hunger, setHunger] = useState<HungerLevel>('medium')
  const [mealContext, setMealContext] = useState('')
  const [timeAvailable, setTimeAvailable] = useState('')
  const [showDetails, setShowDetails] = useState(false)
  const [currentPlace, setCurrentPlace] = useState('')
  const [lastMeal, setLastMeal] = useState('')
  const [hunger10, setHunger10] = useState('')
  const [cookingAccess, setCookingAccess] = useState('')
  const [budgetContext, setBudgetContext] = useState('')
  const [preferenceNote, setPreferenceNote] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  function addFood() {
    const val = inputFood.trim()
    if (val && !foods.includes(val) && foods.length < 20) {
      setFoods((prev) => [...prev, val])
      setInputFood('')
      inputRef.current?.focus()
    }
  }

  function removeFood(f: string) {
    setFoods((prev) => prev.filter((x) => x !== f))
  }

  function handleFoodKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault()
      addFood()
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const result = await whatToEatNow({
        available_foods: foods,
        hunger_level: hunger,
        meal_context: mealContext.trim() || undefined,
        time_available_minutes: timeAvailable ? parseInt(timeAvailable) : undefined,
        current_place: currentPlace.trim() || undefined,
        last_meal_summary: lastMeal.trim() || undefined,
        hunger_level_1_10: hunger10 ? parseInt(hunger10) : undefined,
        cooking_access: cookingAccess.trim() || undefined,
        budget_context: budgetContext.trim() || undefined,
        user_preference_note: preferenceNote.trim() || undefined,
      })
      onResult(result)
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        router.replace(`/${locale}/login`)
        return
      }
      if (err instanceof ApiRequestError) {
        setError(err.status >= 500 ? dict.errors.generic : dict.errors.generic)
        return
      }
      setError(dict.errors.generic)
    } finally {
      setLoading(false)
    }
  }

  const hungerLevels: { value: HungerLevel; label: string }[] = [
    { value: 'low', label: dict.whatToEat.hungerLow },
    { value: 'medium', label: dict.whatToEat.hungerMedium },
    { value: 'high', label: dict.whatToEat.hungerHigh },
  ]

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Food tags */}
      <div>
        <label className="block text-sm font-medium text-ink mb-2">
          {dict.whatToEat.availableFoodsLabel}
        </label>
        {foods.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-3">
            {foods.map((f) => (
              <span
                key={f}
                className="flex items-center gap-1 px-3 py-1.5 rounded-full bg-brand-muted text-brand text-sm font-medium"
              >
                {f}
                <button
                  type="button"
                  onClick={() => removeFood(f)}
                  className="text-brand-light hover:text-brand transition-colors"
                  aria-label={dict.whatToEat.removeFoodAriaLabel.replace('{food}', f)}
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        )}
        <div className="flex gap-2">
          <input
            ref={inputRef}
            type="text"
            value={inputFood}
            onChange={(e) => setInputFood(e.target.value)}
            onKeyDown={handleFoodKeyDown}
            placeholder={dict.whatToEat.availableFoodsPlaceholder}
            className="flex-1 px-4 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
          />
          <button
            type="button"
            onClick={addFood}
            className="px-4 py-3 rounded-2xl bg-brand-muted text-brand text-sm font-medium"
          >
            {dict.whatToEat.addFood}
          </button>
        </div>
        <p className="text-xs text-ink-3 mt-1">{dict.whatToEat.availableFoodsHint}</p>
      </div>

      {/* Hunger level */}
      <div>
        <label className="block text-sm font-medium text-ink mb-2">
          {dict.whatToEat.hungerLevelLabel}
        </label>
        <div className="flex gap-2">
          {hungerLevels.map((h) => (
            <button
              key={h.value}
              type="button"
              onClick={() => setHunger(h.value)}
              className={[
                'flex-1 py-2.5 rounded-2xl text-sm font-medium border transition-colors',
                hunger === h.value
                  ? 'bg-brand text-elevated border-brand'
                  : 'bg-surface border-line text-ink-2',
              ].join(' ')}
            >
              {h.label}
            </button>
          ))}
        </div>
      </div>

      {/* Context + time */}
      <div className="grid grid-cols-2 gap-3">
        <div>
          <label className="block text-xs font-medium text-ink mb-2">
            {dict.whatToEat.timeAvailableLabel}
          </label>
          <input
            type="number"
            value={timeAvailable}
            onChange={(e) => setTimeAvailable(e.target.value)}
            placeholder={dict.whatToEat.timeAvailablePlaceholder}
            min={1}
            max={180}
            className="w-full px-3 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
          />
        </div>
        <div>
          <label className="block text-xs font-medium text-ink mb-2">
            {dict.whatToEat.mealContextLabel}
          </label>
          <input
            type="text"
            value={mealContext}
            onChange={(e) => setMealContext(e.target.value)}
            placeholder={dict.whatToEat.mealContextPlaceholder}
            maxLength={500}
            className="w-full px-3 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
          />
        </div>
      </div>

      <div className="rounded-2xl bg-surface border border-line">
        <button
          type="button"
          onClick={() => setShowDetails((v) => !v)}
          className="w-full px-4 py-3 text-sm font-bold text-ink flex items-center justify-between"
          aria-expanded={showDetails}
        >
          {dict.whatToEat.optionalDetails}
          <span className="text-ink-3">{showDetails ? '−' : '+'}</span>
        </button>
        {showDetails && (
          <div className="px-4 pb-4 space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="wte-place" className="block text-xs font-medium text-ink mb-2">
                  {dict.whatToEat.currentPlaceLabel}
                </label>
                <input
                  id="wte-place"
                  type="text"
                  value={currentPlace}
                  onChange={(e) => setCurrentPlace(e.target.value)}
                  placeholder={dict.whatToEat.currentPlacePlaceholder}
                  maxLength={100}
                  className="w-full px-3 py-3 rounded-2xl bg-elevated border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
                />
              </div>
              <div>
                <label htmlFor="wte-hunger-10" className="block text-xs font-medium text-ink mb-2">
                  {dict.whatToEat.hungerScaleLabel}
                </label>
                <input
                  id="wte-hunger-10"
                  type="number"
                  min={1}
                  max={10}
                  value={hunger10}
                  onChange={(e) => setHunger10(e.target.value)}
                  className="w-full px-3 py-3 rounded-2xl bg-elevated border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
                />
              </div>
            </div>
            <div>
              <label htmlFor="wte-last-meal" className="block text-xs font-medium text-ink mb-2">
                {dict.whatToEat.lastMealLabel}
              </label>
              <input
                id="wte-last-meal"
                type="text"
                value={lastMeal}
                onChange={(e) => setLastMeal(e.target.value)}
                placeholder={dict.whatToEat.lastMealPlaceholder}
                maxLength={300}
                className="w-full px-3 py-3 rounded-2xl bg-elevated border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="wte-cooking" className="block text-xs font-medium text-ink mb-2">
                  {dict.whatToEat.cookingAccessLabel}
                </label>
                <input
                  id="wte-cooking"
                  type="text"
                  value={cookingAccess}
                  onChange={(e) => setCookingAccess(e.target.value)}
                  placeholder={dict.whatToEat.cookingAccessPlaceholder}
                  maxLength={200}
                  className="w-full px-3 py-3 rounded-2xl bg-elevated border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
                />
              </div>
              <div>
                <label htmlFor="wte-budget" className="block text-xs font-medium text-ink mb-2">
                  {dict.whatToEat.budgetContextLabel}
                </label>
                <input
                  id="wte-budget"
                  type="text"
                  value={budgetContext}
                  onChange={(e) => setBudgetContext(e.target.value)}
                  placeholder={dict.whatToEat.budgetContextPlaceholder}
                  maxLength={200}
                  className="w-full px-3 py-3 rounded-2xl bg-elevated border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
                />
              </div>
            </div>
            <div>
              <label htmlFor="wte-preference" className="block text-xs font-medium text-ink mb-2">
                {dict.whatToEat.preferenceNoteLabel}
              </label>
              <input
                id="wte-preference"
                type="text"
                value={preferenceNote}
                onChange={(e) => setPreferenceNote(e.target.value)}
                placeholder={dict.whatToEat.preferenceNotePlaceholder}
                maxLength={500}
                className="w-full px-3 py-3 rounded-2xl bg-elevated border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
              />
            </div>
          </div>
        )}
      </div>

      {error && (
        <p className="text-sm text-error bg-error/5 rounded-xl px-4 py-3">{error}</p>
      )}

      <button
        type="submit"
        disabled={loading}
        className="w-full py-4 rounded-2xl bg-brand text-elevated font-semibold text-sm disabled:opacity-60 transition-opacity"
      >
        {loading ? dict.whatToEat.asking : dict.whatToEat.askBtn}
      </button>
    </form>
  )
}
