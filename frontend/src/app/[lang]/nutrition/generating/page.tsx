'use client'

import { useCallback, useEffect, useRef, useState } from 'react'
import { useParams, useRouter, useSearchParams } from 'next/navigation'
import { DEFAULT_LOCALE, getDictionary, isValidLocale, type Dictionary, type Locale } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import { getMealPlanWeekJob, startMealPlanWeekJob } from '@/lib/nutrition'
import type { GenerateWeekJobStatus } from '@/types/nutrition'

function GeneratingScreen({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const router = useRouter()
  const searchParams = useSearchParams()
  const routerRef = useRef(router)
  routerRef.current = router
  const [error, setError] = useState<string | null>(null)
  const [job, setJob] = useState<GenerateWeekJobStatus | null>(null)
  const calledRef = useRef(false)
  const d = dict.generating

  const run = useCallback(async () => {
    if (calledRef.current) return
    calledRef.current = true
    setError(null)
    try {
      let current = await startMealPlanWeekJob({ locale, force: false })
      setJob(current)
      while (current.status === 'queued' || current.status === 'running') {
        await new Promise(resolve => window.setTimeout(resolve, 1000))
        current = await getMealPlanWeekJob(current.job_id)
        setJob(current)
      }
      if (current.status === 'failed') throw new Error(current.error || d.error)
      const destination = searchParams.get('returnTo') === 'plan' ? 'nutrition/plan' : 'dashboard'
      routerRef.current.replace(`/${locale}/${destination}`)
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        routerRef.current.replace(`/${locale}/login`)
        return
      }
      setError(d.error)
      calledRef.current = false
    }
  }, [locale, d.error, searchParams])

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

  const progress = job?.stage === 'saving_day'
    ? Math.max(75, Math.round(((job.current_day_index || 1) / 7) * 25 + 75))
    : job?.stage === 'reviewing_plan' ? 55
    : job?.stage === 'repairing_plan' ? 65
    : job?.stage === 'generating_plan' ? 30
    : 10

  return (
    <div className="min-h-dvh bg-surface flex flex-col items-center justify-center px-8 space-y-6">
      <div className="w-full max-w-sm space-y-3">
        <div className="h-3 overflow-hidden rounded-full bg-line" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
          <div className="h-full rounded-full bg-brand transition-all duration-500" style={{ width: `${progress}%` }} />
        </div>
        {job?.current_day_index && <p className="text-center text-xs text-ink-3">{job.current_day_index} / {job.total_days}</p>}
      </div>
      <div className="text-center space-y-2">
        <h1 className="text-xl font-bold text-ink">{d.title}</h1>
        <p className="text-sm text-ink-2 leading-relaxed max-w-xs">{d.description}</p>
        {job?.message && <p className="text-sm font-medium text-brand leading-relaxed max-w-xs">{job.message}</p>}
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
