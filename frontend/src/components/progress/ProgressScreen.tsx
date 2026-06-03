'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import type { ProgressSummaryResponse, WeeklyReportResponse } from '@/types/progress'
import { getProgressSummary, getWeeklyReport } from '@/lib/progress'
import CheckInForm from './CheckInForm'
import ProgressSummary from './ProgressSummary'
import WeeklyReport from './WeeklyReport'

interface Props {
  dict: Dictionary
  locale: Locale
}

type Tab = 'summary' | 'weekly'

function todayISODate(): string {
  const d = new Date()
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

export default function ProgressScreen({ dict, locale }: Props) {
  const router = useRouter()
  const [summary, setSummary] = useState<ProgressSummaryResponse | null>(null)
  const [weekly, setWeekly] = useState<WeeklyReportResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [tab, setTab] = useState<Tab>('summary')
  const [showForm, setShowForm] = useState(false)
  const [successMsg, setSuccessMsg] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const [s, w] = await Promise.all([getProgressSummary(), getWeeklyReport()])
      setSummary(s)
      setWeekly(w)
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        router.replace(`/${locale}/login`)
        return
      }
      setLoadError(err instanceof Error ? err.message : dict.progress.errLoadFailed)
    } finally {
      setLoading(false)
    }
  }, [locale, router, dict.progress.errLoadFailed])

  useEffect(() => { void reload() }, [reload])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div
          role="status"
          aria-label={dict.progress.title}
          className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin"
        />
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="flex-1 px-5 pt-6 pb-28">
        <div className="rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-3">
          <p className="text-sm text-error">{loadError}</p>
          <button
            type="button"
            onClick={() => void reload()}
            className="px-4 py-2 rounded-2xl bg-brand text-elevated font-bold text-sm"
          >
            {dict.common.retry}
          </button>
        </div>
      </div>
    )
  }

  const todayLogged =
    summary?.recent_checkins.some((c) => c.check_date === todayISODate()) ?? false

  if (summary && !summary.has_data && !showForm) {
    return (
      <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-ink">{dict.progress.title}</h1>
          <p className="text-sm text-ink-2 mt-1">{dict.progress.subtitle}</p>
        </div>
        <div className="rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-4">
          <div className="mx-auto w-20 h-20 rounded-full bg-brand-muted flex items-center justify-center">
            <span className="text-3xl">⚖️</span>
          </div>
          <h2 className="text-xl font-bold text-ink">{dict.progress.emptyTitle}</h2>
          <p className="text-sm text-ink-2 leading-relaxed">
            {summary.empty_state_message ?? dict.progress.emptyDesc}
          </p>
          <button
            type="button"
            onClick={() => setShowForm(true)}
            className="w-full py-4 rounded-2xl bg-brand text-elevated font-bold text-sm"
          >
            {dict.progress.emptyCheckinCta}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">{dict.progress.title}</h1>
        <p className="text-sm text-ink-2 mt-1">{dict.progress.subtitle}</p>
      </div>

      {!todayLogged && !showForm && (
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="w-full py-3 px-4 rounded-2xl bg-brand-muted text-brand font-bold text-sm text-start"
        >
          {dict.progress.checkInTodayMissing}
        </button>
      )}

      {todayLogged && !showForm && (
        <button
          type="button"
          onClick={() => setShowForm(true)}
          className="w-full py-3 px-4 rounded-2xl bg-surface border border-line text-ink-2 font-bold text-sm text-start"
        >
          {dict.progress.checkInAlreadyToday}
        </button>
      )}

      {showForm && (
        <CheckInForm
          dict={dict}
          onSuccess={() => {
            setShowForm(false)
            setSuccessMsg(dict.progress.checkInSuccess)
            void reload()
            window.setTimeout(() => setSuccessMsg(null), 3000)
          }}
        />
      )}

      {successMsg && !showForm && (
        <p
          role="status"
          className="text-sm text-success bg-brand-muted rounded-xl px-4 py-3 font-bold text-center"
        >
          {successMsg}
        </p>
      )}

      <div className="flex border-b border-line" role="tablist">
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'summary'}
          onClick={() => setTab('summary')}
          className={[
            'flex-1 py-3 text-sm font-bold text-center transition-colors',
            tab === 'summary' ? 'text-brand border-b-2 border-brand' : 'text-ink-3',
          ].join(' ')}
        >
          {dict.progress.tabSummary}
        </button>
        <button
          type="button"
          role="tab"
          aria-selected={tab === 'weekly'}
          onClick={() => setTab('weekly')}
          className={[
            'flex-1 py-3 text-sm font-bold text-center transition-colors',
            tab === 'weekly' ? 'text-brand border-b-2 border-brand' : 'text-ink-3',
          ].join(' ')}
        >
          {dict.progress.tabWeekly}
        </button>
      </div>

      {tab === 'summary' && summary && <ProgressSummary dict={dict} data={summary} />}
      {tab === 'weekly' && weekly && <WeeklyReport dict={dict} data={weekly} />}
    </div>
  )
}
