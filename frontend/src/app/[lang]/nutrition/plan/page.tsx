'use client'

import { useEffect, useState } from 'react'
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
  const [plan, setPlan] = useState<NutritionPlanResponse | null>(null)
  const [profile, setProfile] = useState<NutritionProfileResponse | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getNutritionPlan(), getNutritionProfile()])
      .then(([pl, pr]) => { setPlan(pl); setProfile(pr) })
      .catch((e) => { if (e?.message === 'UNAUTHORIZED') router.replace(`/${locale}/login`) })
      .finally(() => setLoading(false))
  }, [locale, router])

  if (loading) return (
    <div className="flex-1 flex items-center justify-center">
      <div className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin" />
    </div>
  )

  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">{dict.plan.title}</h1>
        <p className="text-sm text-ink-2 mt-1">{dict.plan.subtitle}</p>
      </div>
      {profile?.clinical_review_required && (
        <ClinicalReviewState dict={dict} compact variant="clinical" />
      )}
      {!profile?.clinical_review_required && profile?.risk_level === 'high' && (
        <ClinicalReviewState dict={dict} compact variant="high_risk" />
      )}
      <PlanGenerator
        dict={dict}
        hasPlan={plan?.has_plan ?? false}
        onGenerated={(p) => setPlan(p)}
      />
      {plan?.has_plan && <PlanSummary plan={plan} dict={dict} />}
      {!plan?.has_plan && (
        <div className="rounded-2xl bg-elevated p-8 text-center shadow-sm">
          <p className="text-base font-semibold text-ink mb-2">{dict.plan.noPlanTitle}</p>
          <p className="text-sm text-ink-2">{dict.plan.noPlanDesc}</p>
        </div>
      )}
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
