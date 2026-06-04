'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { api, ApiRequestError } from '@/lib/api'
import { cn } from '@/lib/cn'
import { getIconFlipClass } from '@/lib/direction'
import type { Locale } from '@/lib/i18n'
import { clearToken } from '@/lib/storage'
import type { Dictionary } from '@/dictionaries/fa'

interface Props {
  locale: Locale
  dict: Pick<Dictionary, 'settings' | 'language' | 'common' | 'auth' | 'errors'>
}

interface ProfileData {
  phone: string
}

export default function SettingsScreen({ locale, dict }: Props) {
  const router = useRouter()
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [profile, setProfile] = useState<ProfileData | null>(null)
  const [confirmLogout, setConfirmLogout] = useState(false)
  const [loggingOut, setLoggingOut] = useState(false)

  useEffect(() => {
    let cancelled = false
    async function load() {
      try {
        setLoading(true)
        setLoadError(null)
        const res = await api.get<{ phone: string }>('/api/v1/auth/me', true)
        if (cancelled) return
        setProfile({ phone: res.data.phone })
      } catch (err) {
        if (cancelled) return
        // Canonical UNAUTHORIZED check FIRST (matches ProgressScreen.tsx line 45) —
        // handles the case where an upstream helper wraps the 401 as Error('UNAUTHORIZED').
        if (err instanceof Error && err.message === 'UNAUTHORIZED') {
          router.replace(`/${locale}/login`)
          return
        }
        // Defensive fallback for direct api.get() ApiRequestError with status 401.
        if (err instanceof ApiRequestError && err.status === 401) {
          router.replace(`/${locale}/login`)
          return
        }
        setLoadError(dict.errors.generic)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }
    void load()
    return () => {
      cancelled = true
    }
  }, [dict.errors.generic, locale, router])

  async function handleConfirmLogout() {
    if (loggingOut) return
    setLoggingOut(true)
    try {
      await api.post('/api/v1/auth/logout', {}, true).catch(() => {
        // Even if server logout fails, clear local token
      })
    } finally {
      clearToken()
      router.replace(`/${locale}/login`)
    }
  }

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
            onClick={() => window.location.reload()}
            className="px-4 py-2 rounded-2xl bg-brand text-elevated font-bold text-sm"
          >
            {dict.common.retry}
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28 space-y-6">
      <h1 className="text-xl font-bold text-ink">{dict.settings.title}</h1>

      {/* Language Section */}
      <section className="space-y-2">
        <h2 className="text-xs text-ink-3 font-medium uppercase tracking-wide">
          {dict.settings.languageSection}
        </h2>
        <Link
          href={`/${locale}/settings/language`}
          className="rounded-2xl bg-elevated px-4 py-4 shadow-sm flex items-center justify-between"
        >
          <div className="flex flex-col">
            <span className="text-sm text-ink">{dict.settings.changeLanguage}</span>
            <span className="text-xs text-ink-3">{dict.language[locale]}</span>
          </div>
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={1.8}
            strokeLinecap="round"
            strokeLinejoin="round"
            className={cn('text-ink-3', getIconFlipClass(locale))}
          >
            <polyline points="9 18 15 12 9 6" />
          </svg>
        </Link>
      </section>

      {/* Profile Section */}
      <section className="space-y-2">
        <h2 className="text-xs text-ink-3 font-medium uppercase tracking-wide">
          {dict.settings.profileSection}
        </h2>
        <div className="rounded-2xl bg-elevated px-4 py-4 shadow-sm flex flex-col gap-1">
          <span className="text-xs text-ink-3">{dict.settings.phoneNumber}</span>
          <span className="text-sm text-ink font-medium" dir="ltr">
            {profile?.phone ?? '—'}
          </span>
        </div>
      </section>

      {/* Account Section */}
      <section className="space-y-2">
        <h2 className="text-xs text-ink-3 font-medium uppercase tracking-wide">
          {dict.settings.accountSection}
        </h2>
        {!confirmLogout ? (
          <button
            type="button"
            onClick={() => setConfirmLogout(true)}
            className="w-full rounded-2xl bg-elevated px-4 py-4 shadow-sm text-error text-sm font-semibold text-start"
          >
            {dict.settings.logoutBtn}
          </button>
        ) : (
          <div className="rounded-2xl bg-elevated px-4 py-4 shadow-sm space-y-3">
            <p className="text-sm text-ink leading-relaxed">{dict.settings.logoutConfirm}</p>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setConfirmLogout(false)}
                disabled={loggingOut}
                className="flex-1 py-3 rounded-2xl bg-surface text-ink-2 text-sm font-medium"
              >
                {dict.settings.logoutCancel}
              </button>
              <button
                type="button"
                onClick={handleConfirmLogout}
                disabled={loggingOut}
                className="flex-1 py-3 rounded-2xl bg-brand text-elevated text-sm font-bold"
              >
                {loggingOut ? dict.common.loading : dict.settings.logoutBtn}
              </button>
            </div>
          </div>
        )}
        <p className="text-xs text-ink-3 text-center pt-2">
          {dict.settings.appVersion} 1.0.0
        </p>
      </section>
    </div>
  )
}
