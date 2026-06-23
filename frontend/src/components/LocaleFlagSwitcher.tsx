'use client'

import { useRouter, usePathname } from 'next/navigation'
import {
  LOCALE_COOKIE,
  LOCALE_SRC_COOKIE,
  LOCALE_SRC_MANUAL,
  SUPPORTED_LOCALES,
  type Locale,
} from '@/lib/i18n'
import type { Dictionary } from '@/dictionaries/fa'

const LOCALE_FLAGS: Record<Locale, string> = {
  fa: '🇮🇷',
  en: '🇬🇧',
  ar: '🇸🇦',
}

const COOKIE_MAX_AGE = 60 * 60 * 24 * 365 // 1 year

interface Props {
  locale: Locale
  dict: Pick<Dictionary, 'language'>
}

/**
 * Three-flag language switcher shown on splash, login, and OTP pages.
 * Sets NEXT_LOCALE + NEXT_LOCALE_SRC=manual so the middleware knows this
 * was an explicit user choice (not an automatic cookie written on a previous visit).
 * Preserves the current path + query string when switching locale.
 */
export default function LocaleFlagSwitcher({ locale, dict }: Props) {
  const router = useRouter()
  const pathname = usePathname()

  function handleSelect(newLocale: Locale) {
    if (newLocale === locale) return

    // Write both cookies — locale value + explicit-selection marker
    const cookieOpts = `path=/; max-age=${COOKIE_MAX_AGE}; SameSite=Lax`
    document.cookie = `${LOCALE_COOKIE}=${newLocale}; ${cookieOpts}`
    document.cookie = `${LOCALE_SRC_COOKIE}=${LOCALE_SRC_MANUAL}; ${cookieOpts}`

    // Swap locale segment in current path, preserve query string
    const localePattern = new RegExp(`^/(${SUPPORTED_LOCALES.join('|')})`)
    const newPath = pathname.replace(localePattern, `/${newLocale}`)
    router.push(newPath + window.location.search)
  }

  return (
    <div className="flex flex-col items-center gap-3">
      <p className="text-xs text-ink-3">{dict.language.change}</p>
      {/* dir="ltr" keeps fa→en→ar button order consistent regardless of document direction */}
      <div className="flex items-center gap-3" dir="ltr">
        {SUPPORTED_LOCALES.map((loc) => (
          <button
            key={loc}
            type="button"
            onClick={() => handleSelect(loc)}
            className={[
              'flex flex-col items-center gap-1.5 px-4 py-3 rounded-2xl border transition-colors',
              loc === locale
                ? 'bg-brand-muted border-brand/20 text-brand'
                : 'bg-elevated border-line text-ink-2 hover:text-ink hover:border-ink-3',
            ].join(' ')}
            aria-current={loc === locale ? 'page' : undefined}
            aria-label={dict.language[loc]}
          >
            <span className="text-2xl leading-none" aria-hidden="true">
              {LOCALE_FLAGS[loc]}
            </span>
            <span className={`text-xs ${loc === locale ? 'font-semibold' : 'font-medium'}`}>
              {dict.language[loc]}
            </span>
          </button>
        ))}
      </div>
    </div>
  )
}
