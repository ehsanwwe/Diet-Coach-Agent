'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { DEFAULT_LOCALE, isValidLocale, getDictionary, type Locale, type Dictionary } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import MealCalendar from '@/components/nutrition/MealCalendar'
import ClinicalReviewState from '@/components/nutrition/ClinicalReviewState'
import { getMealPlanCalendar, getNutritionProfile } from '@/lib/nutrition'
import type { CalendarResponse, NutritionProfileResponse } from '@/types/nutrition'
import AppIcon from '@/components/ui/AppIcon'

function PlanScreen({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const router = useRouter()
  const routerRef = useRef(router)
  routerRef.current = router
  const [calendar, setCalendar] = useState<CalendarResponse | null>(null)
  const [profile, setProfile] = useState<NutritionProfileResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [generating, setGenerating] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [genError, setGenError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const [cal, pr] = await Promise.all([
        getMealPlanCalendar({ locale, days: 30 }),
        getNutritionProfile(),
      ])
      setCalendar(cal)
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

  const handleGenerate = useCallback(async () => {
    setGenerating(true)
    setGenError(null)
    router.push(`/${locale}/nutrition/generating?returnTo=plan`)
  }, [locale, router])

  const d = dict.calendar

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div role="status" aria-label={dict.common.loading}
          className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin" />
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="flex-1 px-5 pt-6 pb-28">
        <div className="rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-3">
          <p className="text-sm text-error">{loadError}</p>
          <button type="button" onClick={() => void reload()}
            className="px-4 py-2 rounded-2xl bg-brand text-elevated font-bold text-sm">
            {dict.common.retry}
          </button>
        </div>
      </div>
    )
  }

  const hasDays = (calendar?.days.length ?? 0) > 0
  const isClinical = profile?.clinical_review_required ?? false
  const isHighRisk = !isClinical && profile?.risk_level === 'high'

  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-ink">{d.title}</h1>
        <p className="text-sm text-ink-2 mt-1">{d.subtitle}</p>
      </div>

      {isClinical && <ClinicalReviewState dict={dict} compact variant="clinical" />}
      {isHighRisk && <ClinicalReviewState dict={dict} compact variant="high_risk" />}

      {genError && (
        <div className="rounded-xl bg-error/5 border border-error/20 px-4 py-3">
          <p className="text-sm text-error">{genError}</p>
        </div>
      )}

      {!hasDays ? (
        <div className="rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-4">
          <div className="mx-auto w-20 h-20 rounded-full bg-brand-muted flex items-center justify-center">
            <AppIcon name="calendar" className="text-brand" size={34} />
          </div>
          <h2 className="text-xl font-bold text-ink">{d.noPlanTitle}</h2>
          <p className="text-sm text-ink-2 leading-relaxed">{d.noPlanDesc}</p>
          <button type="button" disabled={generating} onClick={handleGenerate}
            className="w-full py-4 rounded-2xl bg-brand text-elevated font-semibold text-sm disabled:opacity-60">
            {generating ? d.generationLoading : d.generateInitialWeek}
          </button>
        </div>
      ) : (
        <MealCalendar
          calendar={calendar!}
          dict={dict}
          locale={locale}
          onGenerateNextWeek={handleGenerate}
          generating={generating}
        />
      )}
    </div>
  )
}

export default function PlanPage() {
  const params = useParams()
  const lang = params.lang as string
  const locale: Locale = isValidLocale(lang) ? lang : DEFAULT_LOCALE
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
