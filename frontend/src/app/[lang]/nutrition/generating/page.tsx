'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { DEFAULT_LOCALE, getDictionary, isValidLocale, type Dictionary, type Locale } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import { generateMealPlanWeek } from '@/lib/nutrition'

function GeneratingScreen({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const router = useRouter()
  const routerRef = useRef(router)
  routerRef.current = router
  const [error, setError] = useState<string | null>(null)
  const calledRef = useRef(false)
  const d = dict.generating

  const run = useCallback(async () => {
    if (calledRef.current) return
    calledRef.current = true
    setError(null)
    try {
      // force=false: returns existing plan if one already exists (idempotent)
      await generateMealPlanWeek({ locale, force: false })
      routerRef.current.replace(`/${locale}/dashboard`)
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        routerRef.current.replace(`/${locale}/login`)
        return
      }
      setError(d.error)
      calledRef.current = false
    }
  }, [locale, d.error])

  useEffect(() => {
    void run()
  }, [run])

  if (error) {
    return (
      <div className="min-h-dvh bg-surface flex items-center justify-center px-8">
        <div className="text-center space-y-5">
          <p className="text-sm text-error leading-relaxed max-w-xs">{error}</p>
          <button
            type="button"
            onClick={() => { void run() }}
            className="px-6 py-3 rounded-2xl bg-brand text-elevated font-semibold text-sm"
          >
            {d.retry}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-dvh bg-surface flex flex-col items-center justify-center px-8 space-y-6">
      <div className="w-16 h-16 rounded-full border-[3px] border-brand border-t-transparent animate-spin" />
      <div className="text-center space-y-2">
        <h1 className="text-xl font-bold text-ink">{d.title}</h1>
        <p className="text-sm text-ink-2 leading-relaxed max-w-xs">{d.description}</p>
      </div>
    </div>
  )
}

export default function GeneratingPage() {
  const params = useParams()
  const lang = params.lang as string
  const locale: Locale = isValidLocale(lang) ? lang : DEFAULT_LOCALE
  const [dict, setDict] = useState<Dictionary | null>(null)
  useEffect(() => { getDictionary(locale).then(setDict) }, [locale])
  if (!dict) return null
  return (
    <AuthGuard locale={locale}>
      <GeneratingScreen locale={locale} dict={dict} />
    </AuthGuard>
  )
}
