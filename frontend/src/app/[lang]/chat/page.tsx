'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'
import { isValidLocale, getDictionary, type Locale, type Dictionary } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import CompanionChat from '@/components/chat/CompanionChat'

export default function ChatPage() {
  const params = useParams()
  const lang = params.lang as string
  if (!isValidLocale(lang)) return null
  const locale = lang as Locale
  const [dict, setDict] = useState<Dictionary | null>(null)
  useEffect(() => { getDictionary(locale).then(setDict) }, [locale])
  if (!dict) return null
  return (
    <AuthGuard locale={locale}>
      <div className="app-container flex flex-col pb-24" style={{ height: '100dvh' }}>
        <div className="px-5 pt-6 pb-3 border-b border-line shrink-0">
          <h1 className="text-xl font-bold text-ink">{dict.companionChat.title}</h1>
          <p className="text-xs text-ink-2 mt-0.5">{dict.companionChat.subtitle}</p>
        </div>
        <CompanionChat dict={dict} locale={locale} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
