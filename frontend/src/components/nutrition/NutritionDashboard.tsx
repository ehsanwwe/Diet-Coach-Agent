'use client'

import Link from 'next/link'
import { useCallback, useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import type { CalendarResponse, NutritionPlanResponse, NutritionProfileResponse } from '@/types/nutrition'
import { getMealPlanCalendar, getNutritionPlan, getNutritionProfile } from '@/lib/nutrition'
import ClinicalReviewState from './ClinicalReviewState'
import AppIcon, { type AppIconName } from '@/components/ui/AppIcon'

interface Props {
  dict: Dictionary
  locale: Locale
}

function QuickActionCard({ href, icon, label, className }: { href: string; icon: AppIconName; label: string; className?: string }) {
  return (
    <Link
      href={href}
      className={['flex flex-col items-center gap-2 p-4 rounded-2xl bg-elevated shadow-sm hover:shadow-md transition-shadow', className].filter(Boolean).join(' ')}
    >
      <AppIcon name={icon} className="text-brand" size={24} />
      <span className="text-xs font-medium text-ink-2 text-center leading-tight">{label}</span>
    </Link>
  )
}

export default function NutritionDashboard({ dict, locale }: Props) {
  const router = useRouter()
  const routerRef = useRef(router)
  routerRef.current = router
  const [profile, setProfile] = useState<NutritionProfileResponse | null>(null)
  const [plan, setPlan] = useState<NutritionPlanResponse | null>(null)
  const [calendar, setCalendar] = useState<CalendarResponse | null>(null)
  const [generating, setGenerating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    setLoading(true)
    setLoadError(null)
    try {
      const [p, pl, cal] = await Promise.all([
        getNutritionProfile(),
        getNutritionPlan(),
        getMealPlanCalendar({ locale, days: 14 }),
      ])
      setProfile(p)
      setPlan(pl)
      setCalendar(cal)
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

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div
          role="status"
          aria-label={dict.common.loading}
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

  const isClinical = profile?.clinical_review_required ?? false
  const riskLevel = profile?.risk_level ?? 'low'
  const renewal = calendar?.renewal_status
  const hasCalendarPlan =
    Boolean(calendar?.calendar_id) ||
    (calendar?.days?.length ?? 0) > 0 ||
    (calendar?.coverage?.planned_days_count ?? 0) > 0
  const hasAnyPlan = plan?.has_plan === true || hasCalendarPlan
  const showNextWeekPreparationCard = Boolean(renewal?.should_prompt_next_week)
  const shouldHideEmptyPlanCard = showNextWeekPreparationCard && !hasAnyPlan

  async function handleGenerateNextWeek() {
    setGenerating(true)
    router.push(`/${locale}/nutrition/generating`)
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-ink">
          {dict.dashboard.greetingGeneric}
        </h1>
        <p className="text-sm text-ink-2 mt-1">{dict.dashboard.subtitle}</p>
      </div>

      {/* Next-week renewal banner */}
      {renewal?.should_prompt_next_week && (
        <div className={[
          'rounded-2xl p-4 space-y-3',
          renewal.prompt_level === 'warning' ? 'bg-warm-muted border border-warm/30' : 'bg-brand-muted border border-brand/20',
        ].join(' ')}>
          <div>
            <p className="text-sm font-semibold text-ink">{dict.calendar.nextWeekPromptTitle}</p>
            <p className="text-xs text-ink-2 mt-1">{dict.calendar.nextWeekPromptDescription}</p>
          </div>
          <button type="button" disabled={generating} onClick={() => void handleGenerateNextWeek()}
            className="w-full py-3 rounded-xl bg-brand text-elevated font-semibold text-sm disabled:opacity-60">
            {generating ? dict.calendar.generationLoading : dict.calendar.nextWeekPromptCta}
          </button>
        </div>
      )}

      {/* Clinical alert */}
      {isClinical && (
        <ClinicalReviewState dict={dict} compact variant="clinical" />
      )}
      {!isClinical && riskLevel === 'high' && (
        <ClinicalReviewState dict={dict} compact variant="high_risk" />
      )}

      {/* Onboarding incomplete */}
      {profile && !profile.onboarding_complete && (
        <div className="rounded-2xl bg-warm-muted border border-warm/20 p-4 flex items-center justify-between gap-4">
          <p className="text-sm font-medium text-ink">{dict.dashboard.noOnboarding}</p>
          <Link
            href={`/${locale}/onboarding`}
            className="text-sm font-semibold text-brand shrink-0"
          >
            {dict.dashboard.noOnboardingCta}
          </Link>
        </div>
      )}

      {/* Current plan summary — hidden when next-week renewal banner is visible and no plan exists */}
      {!shouldHideEmptyPlanCard && <div className="rounded-2xl bg-elevated p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-ink">
            {hasAnyPlan ? dict.dashboard.currentPlanLabel : dict.dashboard.noPlanTitle}
          </h2>
          {profile && (
            <span className={[
              'text-xs px-2 py-0.5 rounded-full font-medium',
              riskLevel === 'low' ? 'bg-success/10 text-success' :
              riskLevel === 'medium' ? 'bg-brand-muted text-brand' :
              'bg-warm-muted text-warm',
            ].join(' ')}>
              {dict.dashboard[
                isClinical ? 'riskClinical' :
                riskLevel === 'low' ? 'riskLow' :
                riskLevel === 'medium' ? 'riskMedium' : 'riskHigh'
              ]}
            </span>
          )}
        </div>
        {plan?.has_plan && plan.summary ? (
          <p className="text-sm text-ink-2 leading-relaxed">{plan.summary}</p>
        ) : hasCalendarPlan ? (
          <p className="text-sm text-ink-2">{dict.dashboard.calendarPlanDesc}</p>
        ) : (
          <p className="text-sm text-ink-2">{dict.dashboard.noPlanDesc}</p>
        )}
        <Link
          href={`/${locale}/nutrition/plan`}
          className="mt-4 block text-center py-3 rounded-2xl bg-brand text-elevated font-semibold text-sm"
        >
          {hasAnyPlan ? dict.dashboard.currentPlanLabel : dict.dashboard.noPlanCta}
        </Link>
      </div>}

      {/* Quick actions */}
      <div>
        <h2 className="text-sm font-semibold text-ink mb-3">{dict.dashboard.quickActionsTitle}</h2>
        <div className="grid grid-cols-2 gap-3">
          <QuickActionCard
            href={`/${locale}/nutrition/meal-analysis`}
            icon="search"
            label={dict.dashboard.analyzeMeal}
          />
          <QuickActionCard
            href={`/${locale}/nutrition/what-to-eat`}
            icon="question"
            label={dict.dashboard.whatToEatNow}
          />
          <QuickActionCard
            href={`/${locale}/nutrition/plan`}
            icon="clipboardList"
            label={dict.dashboard.generatePlan}
          />
          <QuickActionCard
            href={`/${locale}/chat`}
            icon="chat"
            label={dict.dashboard.openChat}
          />
          <QuickActionCard
            href={`/${locale}/behavior-guide`}
            icon="brain"
            label={dict.dashboard.behaviorGuide}
            className="col-span-2"
          />
        </div>
      </div>
    </div>
  )
}
