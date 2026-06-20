'use client'

import { useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { DEFAULT_LOCALE, isValidLocale, getDictionary, type Locale, type Dictionary } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import MealAnalysisForm from '@/components/nutrition/MealAnalysisForm'
import MealAnalysisResult from '@/components/nutrition/MealAnalysisResult'
import type { MealAnalysisResponse } from '@/types/nutrition'

function MealAnalysisScreen({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const router = useRouter()
  const routerRef = useRef(router)
  routerRef.current = router
  const [result, setResult] = useState<MealAnalysisResponse | null>(null)

  function handleResult(r: MealAnalysisResponse) {
    if ((r as unknown as { detail?: { message?: string } })?.detail?.message === 'UNAUTHORIZED') {
      routerRef.current.replace(`/${locale}/login`)
      return
    }
    setResult(r)
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">{dict.mealAnalysis.title}</h1>
        <p className="text-sm text-ink-2 mt-1">{dict.mealAnalysis.subtitle}</p>
      </div>
      {!result ? (
        <MealAnalysisForm dict={dict} locale={locale} onResult={handleResult} />
      ) : (
        <MealAnalysisResult result={result} dict={dict} onReset={() => setResult(null)} />
      )}
    </div>
  )
}

export default function MealAnalysisPage() {
  const params = useParams()
  const lang = params.lang as string
  const locale: Locale = isValidLocale(lang) ? lang : DEFAULT_LOCALE
  const [dict, setDict] = useState<Dictionary | null>(null)
  useEffect(() => { getDictionary(locale).then(setDict) }, [locale])
  if (!dict) return null
  return (
    <AuthGuard locale={locale}>
      <div className="app-container">
        <MealAnalysisScreen locale={locale} dict={dict} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
