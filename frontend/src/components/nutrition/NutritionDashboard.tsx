'use client'

import Link from 'next/link'
import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import type { NutritionPlanResponse, NutritionProfileResponse } from '@/types/nutrition'
import { getNutritionPlan, getNutritionProfile } from '@/lib/nutrition'
import ClinicalReviewState from './ClinicalReviewState'

interface Props {
  dict: Dictionary
  locale: Locale
}

function QuickActionCard({ href, icon, label }: { href: string; icon: string; label: string }) {
  return (
    <Link
      href={href}
      className="flex flex-col items-center gap-2 p-4 rounded-2xl bg-elevated shadow-sm hover:shadow-md transition-shadow"
    >
      <span className="text-2xl">{icon}</span>
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
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    Promise.all([getNutritionProfile(), getNutritionPlan()])
      .then(([p, pl]) => { setProfile(p); setPlan(pl) })
      .catch((err) => {
        if (err?.message === 'UNAUTHORIZED') routerRef.current.replace(`/${locale}/login`)
      })
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale])

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin" />
      </div>
    )
  }

  const isClinical = profile?.clinical_review_required ?? false
  const riskLevel = profile?.risk_level ?? 'low'

  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
      {/* Greeting */}
      <div>
        <h1 className="text-2xl font-bold text-ink">
          {dict.dashboard.greetingGeneric}
        </h1>
        <p className="text-sm text-ink-2 mt-1">{dict.dashboard.subtitle}</p>
      </div>

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

      {/* Current plan summary */}
      <div className="rounded-2xl bg-elevated p-5 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-sm font-semibold text-ink">
            {plan?.has_plan ? dict.dashboard.currentPlanLabel : dict.dashboard.noPlanTitle}
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
        ) : (
          <p className="text-sm text-ink-2">{dict.dashboard.noPlanDesc}</p>
        )}
        <Link
          href={`/${locale}/nutrition/plan`}
          className="mt-4 block text-center py-3 rounded-2xl bg-brand text-elevated font-semibold text-sm"
        >
          {plan?.has_plan ? dict.dashboard.currentPlanLabel : dict.dashboard.noPlanCta}
        </Link>
      </div>

      {/* Quick actions */}
      <div>
        <h2 className="text-sm font-semibold text-ink mb-3">{dict.dashboard.quickActionsTitle}</h2>
        <div className="grid grid-cols-2 gap-3">
          <QuickActionCard
            href={`/${locale}/nutrition/meal-analysis`}
            icon="🍽️"
            label={dict.dashboard.analyzeMeal}
          />
          <QuickActionCard
            href={`/${locale}/nutrition/what-to-eat`}
            icon="🤔"
            label={dict.dashboard.whatToEatNow}
          />
          <QuickActionCard
            href={`/${locale}/nutrition/plan`}
            icon="📋"
            label={dict.dashboard.generatePlan}
          />
          <QuickActionCard
            href={`/${locale}/chat`}
            icon="💬"
            label={dict.dashboard.openChat}
          />
        </div>
      </div>
    </div>
  )
}
