'use client'

import { useState } from 'react'
import type { Dictionary } from '@/dictionaries/fa'
import type { MealAnalysisResponse } from '@/types/nutrition'
import { analyzeMeal } from '@/lib/nutrition'

type MealTime = 'breakfast' | 'lunch' | 'dinner' | 'snack' | 'unknown'

interface Props {
  dict: Pick<Dictionary, 'mealAnalysis' | 'common'>
  onResult: (result: MealAnalysisResponse) => void
}

export default function MealAnalysisForm({ dict, onResult }: Props) {
  const [mealText, setMealText] = useState('')
  const [mealTime, setMealTime] = useState<MealTime>('unknown')
  const [context, setContext] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const mealTimes: { value: MealTime; label: string }[] = [
    { value: 'breakfast', label: dict.mealAnalysis.breakfast },
    { value: 'lunch', label: dict.mealAnalysis.lunch },
    { value: 'dinner', label: dict.mealAnalysis.dinner },
    { value: 'snack', label: dict.mealAnalysis.snack },
    { value: 'unknown', label: dict.mealAnalysis.unknown },
  ]

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!mealText.trim()) return
    setLoading(true)
    setError(null)
    try {
      const result = await analyzeMeal({
        meal_text: mealText.trim(),
        meal_time: mealTime,
        context: context.trim() || undefined,
      })
      onResult(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : dict.common.error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      <div>
        <label className="block text-sm font-medium text-ink mb-2">
          {dict.mealAnalysis.mealDescLabel}
        </label>
        <textarea
          value={mealText}
          onChange={(e) => setMealText(e.target.value)}
          placeholder={dict.mealAnalysis.mealDescPlaceholder}
          rows={4}
          maxLength={2000}
          required
          className="w-full px-4 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 resize-none focus:outline-none focus:border-brand transition-colors"
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-ink mb-2">
          {dict.mealAnalysis.mealTimeLabel}
        </label>
        <div className="flex flex-wrap gap-2">
          {mealTimes.map((mt) => (
            <button
              key={mt.value}
              type="button"
              onClick={() => setMealTime(mt.value)}
              className={[
                'px-4 py-2 rounded-full text-sm font-medium border transition-colors',
                mealTime === mt.value
                  ? 'bg-brand text-elevated border-brand'
                  : 'bg-surface border-line text-ink-2',
              ].join(' ')}
            >
              {mt.label}
            </button>
          ))}
        </div>
      </div>

      <div>
        <label className="block text-sm font-medium text-ink mb-2">
          {dict.mealAnalysis.contextLabel}
        </label>
        <input
          type="text"
          value={context}
          onChange={(e) => setContext(e.target.value)}
          placeholder={dict.mealAnalysis.contextPlaceholder}
          maxLength={500}
          className="w-full px-4 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 focus:outline-none focus:border-brand transition-colors"
        />
      </div>

      {error && (
        <p className="text-sm text-error bg-error/5 rounded-xl px-4 py-3">{error}</p>
      )}

      <button
        type="submit"
        disabled={loading || !mealText.trim()}
        className="w-full py-4 rounded-2xl bg-brand text-elevated font-semibold text-sm disabled:opacity-60 transition-opacity"
      >
        {loading ? dict.mealAnalysis.analyzing : dict.mealAnalysis.analyzeBtn}
      </button>
    </form>
  )
}
