'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { DEFAULT_LOCALE, isValidLocale, getDictionary, type Locale, type Dictionary } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import BehaviorCoaching from '@/components/nutrition/BehaviorCoaching'

function BehaviorGuideScreen({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
      <BehaviorCoaching dict={dict} locale={locale} />
    </div>
  )
}

export default function BehaviorGuidePage() {
  const params = useParams()
  const lang = params.lang as string
  const locale: Locale = isValidLocale(lang) ? lang : DEFAULT_LOCALE
  const [dict, setDict] = useState<Dictionary | null>(null)
  useEffect(() => { getDictionary(locale).then(setDict) }, [locale])
  if (!dict) return null
  return (
    <AuthGuard locale={locale}>
      <div className="app-container">
        <BehaviorGuideScreen locale={locale} dict={dict} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
