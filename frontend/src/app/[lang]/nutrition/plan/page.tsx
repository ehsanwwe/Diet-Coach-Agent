'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { isValidLocale, getDictionary, type Locale, type Dictionary } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import PlanSummary from '@/components/nutrition/PlanSummary'
import PlanGenerator from '@/components/nutrition/PlanGenerator'
import ClinicalReviewState from '@/components/nutrition/ClinicalReviewState'
import { getNutritionPlan, getNutritionProfile } from '@/lib/nutrition'
import type { NutritionPlanResponse, NutritionProfileResponse } from '@/types/nutrition'

function PlanScreen({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const router = useRouter()
  const routerRef = useRef(router)
  routerRef.current = router
  const [plan, setPlan] = useState<NutritionPlanResponse | null>(null)
  const [profile, setProfile] = useState<NutritionProfileResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const [pl, pr] = await Promise.all([getNutritionPlan(), getNutritionProfile()])
      setPlan(pl)
      setProfile(pr)
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        routerRef.current.replace(`/${locale}/login`)
        return
      }
      setLoadError(dict.errors.generic)
    } finally {
      setLoading(false)
    }
  }, [locale, dict.errors.generic])

  useEffect(() => { void reload() }, [reload])

  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">{dict.plan.title}</h1>
        <p className="text-sm text-ink-2 mt-1">{dict.plan.subtitle}</p>
      </div>
      {!loading && !loadError && profile?.clinical_review_required && (
        <ClinicalReviewState dict={dict} compact variant="clinical" />
      )}
      {!loading && !loadError && !profile?.clinical_review_required && profile?.risk_level === 'high' && (
        <ClinicalReviewState dict={dict} compact variant="high_risk" />
      )}
      {!loading && !loadError && (
        <PlanGenerator
          dict={dict}
          hasPlan={plan?.has_plan ?? false}
          onGenerated={(p) => setPlan(p)}
        />
      )}
      <PlanSummary
        plan={plan?.has_plan ? plan : null}
        loading={loading}
        loadError={loadError}
        onRetry={() => void reload()}
        dict={dict}
      />
    </div>
  )
}

export default function PlanPage() {
  const params = useParams()
  const lang = params.lang as string
  if (!isValidLocale(lang)) return null
  const locale = lang as Locale
  const [dict, setDict] = useState<Dictionary | null>(null)
  useEffect(() => { getDictionary(locale).then(setDict) }, [locale])
  if (!dict) return null
  return (
    <AuthGuard locale={locale}>
      <div className="app-container">
        <PlanScreen locale={locale} dict={dict} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
