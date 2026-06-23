'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import { useAuth } from '@/hooks/useAuth'
import LocaleFlagSwitcher from '@/components/LocaleFlagSwitcher'

interface Props {
  dict: Dictionary
  locale: Locale
}

function AppIcon() {
  return (
    <svg
      width="44"
      height="44"
      viewBox="0 0 44 44"
      fill="none"
      aria-hidden="true"
      role="img"
    >
      <line
        x1="22"
        y1="40"
        x2="22"
        y2="22"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
      <path
        d="M22 22 C22 22 36 18 36 8 C36 8 24 7 22 22"
        fill="currentColor"
        opacity="0.9"
      />
      <path
        d="M22 30 C22 30 10 27 10 17 C10 17 20 18 22 30"
        fill="currentColor"
        opacity="0.65"
      />
    </svg>
  )
}

function Spinner() {
  return (
    <div className="min-h-dvh bg-surface flex items-center justify-center">
      <div className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin" />
    </div>
  )
}

/**
 * Shown at /[lang]. Redirects authenticated users to the dashboard;
 * unauthenticated users see the splash / marketing page.
 */
export default function SplashOrRedirect({ dict, locale }: Props) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace(`/${locale}/dashboard`)
    }
  }, [isLoading, isAuthenticated, locale, router])

  if (isLoading) return <Spinner />
  if (isAuthenticated) return <Spinner />

  return (
    <div className="min-h-dvh bg-surface flex flex-col">
      <div className="app-container flex-1 flex flex-col items-center justify-center px-8 py-16 text-center">

        <div className="w-20 h-20 rounded-full bg-brand-muted flex items-center justify-center mb-8 text-brand">
          <AppIcon />
        </div>
        <div className="flex pb-8 flex-col items-center">
          <LocaleFlagSwitcher locale={locale} dict={dict} />
        </div>
        <h1 className="text-3xl font-bold text-ink mb-3 leading-tight">
          {dict.common.appName}
        </h1>

        <p className="text-base font-medium text-brand mb-4">
          {dict.splash.tagline}
        </p>

        <p className="text-sm text-ink-2 leading-relaxed max-w-[300px] mb-12">
          {dict.splash.description}
        </p>

        <div className="flex flex-col items-center gap-3 w-full max-w-[280px]">
          <a
            href={`/${locale}/login`}
            className="w-full text-center py-4 rounded-2xl bg-brand text-elevated font-semibold text-sm"
          >
            {dict.splash.getStarted}
          </a>
        </div>
      </div>

    </div>
  )
}
