'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { isValidLocale, getDictionary, type Locale, type Dictionary } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import WhatToEatForm from '@/components/nutrition/WhatToEatForm'
import WhatToEatResult from '@/components/nutrition/WhatToEatResult'
import type { WhatToEatNowResponse } from '@/types/nutrition'

function WhatToEatScreen({ locale, dict }: { locale: Locale; dict: Dictionary }) {
  const [result, setResult] = useState<WhatToEatNowResponse | null>(null)
  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-ink">{dict.whatToEat.title}</h1>
        <p className="text-sm text-ink-2 mt-1">{dict.whatToEat.subtitle}</p>
      </div>
      {!result ? (
        <WhatToEatForm dict={dict} onResult={setResult} />
      ) : (
        <WhatToEatResult result={result} dict={dict} onReset={() => setResult(null)} />
      )}
    </div>
  )
}

export default function WhatToEatPage() {
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
        <WhatToEatScreen locale={locale} dict={dict} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
