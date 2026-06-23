'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'
import { ChevronLeft, ChevronRight } from 'lucide-react'
import { api, ApiRequestError } from '@/lib/api'
import { cn } from '@/lib/cn'
import { LOCALE_COOKIE, LOCALE_SRC_COOKIE, LOCALE_SRC_MANUAL, SUPPORTED_LOCALES, type Locale } from '@/lib/i18n'
import type { Dictionary } from '@/dictionaries/fa'

interface Props {
  locale: Locale
  dict: Pick<Dictionary, 'language' | 'settings' | 'common'>
}

export default function LanguageSelector({ locale, dict }: Props) {
  const router = useRouter()
  const [pending, setPending] = useState<Locale | null>(null)
  const isRtl = locale === 'fa' || locale === 'ar'
  const BackIcon = isRtl ? ChevronRight : ChevronLeft

  function handleBack() {
    router.push(`/${locale}/settings`)
  }

  function handleSelect(newLocale: Locale) {
    if (newLocale === locale || pending) return
    setPending(newLocale)

    // 1. Write NEXT_LOCALE + manual-source marker (explicit user selection)
    const cookieOpts = `path=/; max-age=${60 * 60 * 24 * 365}; SameSite=Lax`
    document.cookie = `${LOCALE_COOKIE}=${newLocale}; ${cookieOpts}`
    document.cookie = `${LOCALE_SRC_COOKIE}=${LOCALE_SRC_MANUAL}; ${cookieOpts}`

    // 2. Fire-and-forget backend persist (cookie is canonical client-side; errors silently swallowed)
    void api
      .patch('/api/v1/settings/language', { language_code: newLocale }, true)
      .catch((err: unknown) => {
        if (err instanceof ApiRequestError) return // ignore — cookie already written
      })

    // 3. Navigate to same screen in new locale — server re-renders <html lang dir>
    router.push(`/${newLocale}/settings/language`)
  }

  return (
    <div className="flex flex-col min-h-dvh">
      {/* Header with back navigation */}
      <div className="flex items-center gap-2 px-4 pt-5 pb-3 border-b border-line shrink-0">
        <button
          type="button"
          onClick={handleBack}
          className="flex items-center gap-1 text-brand text-sm font-medium"
          aria-label={dict.language.backToSettings}
        >
          <BackIcon size={18} />
          <span>{dict.language.backToSettings}</span>
        </button>
      </div>

      {/* Language list */}
      <div className="flex-1 overflow-y-auto px-5 pt-5 pb-10 space-y-2">
        <h1 className="text-xl font-bold text-ink mb-4">{dict.language.select}</h1>
        {SUPPORTED_LOCALES.map((loc) => {
          const isActive = loc === locale
          const isPending = pending === loc
          return (
            <button
              key={loc}
              type="button"
              onClick={() => handleSelect(loc)}
              disabled={isPending}
              className={cn(
                'w-full flex items-center justify-between px-4 py-4 rounded-2xl transition-colors',
                isActive
                  ? 'bg-brand-muted text-brand font-bold'
                  : 'bg-elevated text-ink font-medium',
                isPending ? 'opacity-60 cursor-wait' : '',
              )}
            >
              <span className="text-sm">{dict.language[loc]}</span>
              {isActive && (
                <span className="text-xs text-brand">{dict.language.current}</span>
              )}
            </button>
          )
        })}
      </div>
    </div>
  )
}
