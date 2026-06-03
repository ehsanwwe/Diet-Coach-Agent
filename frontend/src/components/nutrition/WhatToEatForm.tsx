'use client'

import { useState, useRef } from 'react'
import type { Dictionary } from '@/dictionaries/fa'
import type { WhatToEatNowResponse } from '@/types/nutrition'
import { whatToEatNow } from '@/lib/nutrition'

type HungerLevel = 'low' | 'medium' | 'high'

interface Props {
  dict: Pick<Dictionary, 'whatToEat' | 'common'>
  onResult: (result: WhatToEatNowResponse) => void
}

export default function WhatToEatForm({ dict, onResult }: Props) {
  const [foods, setFoods] = useState<string[]>([])
  const [inputFood, setInputFood] = useState('')
  const [hunger, setHunger] = useState<HungerLevel>('medium')
  const [mealContext, setMealContext] = useState('')
  const [timeAvailable, setTimeAvailable] = useState('')
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
      })
      onResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : dict.common.error)
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
                  aria-label={`remove ${f}`}
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
