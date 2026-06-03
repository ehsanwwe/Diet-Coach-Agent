'use client'

import { useState } from 'react'
import type { Dictionary } from '@/dictionaries/fa'
import type { NutritionPlanResponse } from '@/types/nutrition'
import { generateNutritionPlan } from '@/lib/nutrition'

interface Props {
  dict: Pick<Dictionary, 'plan' | 'common'>
  hasPlan: boolean
  onGenerated: (plan: NutritionPlanResponse) => void
}

export default function PlanGenerator({ dict, hasPlan, onGenerated }: Props) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleGenerate() {
    setLoading(true)
    setError(null)
    try {
      const plan = await generateNutritionPlan()
      onGenerated(plan)
    } catch (e) {
      setError(e instanceof Error ? e.message : dict.common.error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-3">
      {error && (
        <p className="text-sm text-error bg-error/5 rounded-xl px-4 py-3">{error}</p>
      )}
      <button
        onClick={handleGenerate}
        disabled={loading}
        className="w-full py-4 rounded-2xl bg-brand text-elevated font-semibold text-sm disabled:opacity-60 transition-opacity"
      >
        {loading ? dict.plan.generating : hasPlan ? dict.plan.regenerateBtn : dict.plan.generateBtn}
      </button>
    </div>
  )
}
