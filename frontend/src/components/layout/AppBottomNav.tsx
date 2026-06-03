'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'

interface Props {
  locale: Locale
  dict: Pick<Dictionary, 'nav'>
}

function HomeIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.2 : 1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1H5a1 1 0 01-1-1V9.5z" />
      <path d="M9 21V12h6v9" />
    </svg>
  )
}

function ChatIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.2 : 1.8} strokeLinecap="round" strokeLinejoin="round">
      <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z" />
    </svg>
  )
}

function ProgressIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.2 : 1.8} strokeLinecap="round" strokeLinejoin="round">
      <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
    </svg>
  )
}

function SettingsIcon({ active }: { active: boolean }) {
  return (
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={active ? 2.2 : 1.8} strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3" />
      <path d="M19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 010 2.83 2 2 0 01-2.83 0l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 01-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 01-2.83-2.83l.06-.06A1.65 1.65 0 004.68 15a1.65 1.65 0 00-1.51-1H3a2 2 0 010-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 012.83-2.83l.06.06A1.65 1.65 0 009 4.68a1.65 1.65 0 001-1.51V3a2 2 0 014 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 012.83 2.83l-.06.06A1.65 1.65 0 0019.4 9a1.65 1.65 0 001.51 1H21a2 2 0 010 4h-.09a1.65 1.65 0 00-1.51 1z" />
    </svg>
  )
}

export default function AppBottomNav({ locale, dict }: Props) {
  const pathname = usePathname()

  const isActive = (segment: string) => pathname.includes(`/${segment}`)

  const tabs = [
    {
      href: `/${locale}/dashboard`,
      label: dict.nav.home,
      icon: HomeIcon,
      active: isActive('dashboard') || pathname === `/${locale}`,
      disabled: false,
    },
    {
      href: `/${locale}/chat`,
      label: dict.nav.chat,
      icon: ChatIcon,
      active: isActive('chat'),
      disabled: false,
    },
    {
      href: `/${locale}/progress`,
      label: dict.nav.progress,
      icon: ProgressIcon,
      active: isActive('progress'),
      disabled: false,
    },
    {
      href: `/${locale}/settings`,
      label: dict.nav.settings,
      icon: SettingsIcon,
      active: false,
      disabled: true,
    },
  ]

  return (
    <nav className="fixed bottom-0 inset-x-0 z-50 pb-safe bg-elevated border-t border-line">
      <div className="app-container min-h-0 flex-row flex items-stretch max-w-[430px] mx-auto">
        {tabs.map((tab) => {
          const Icon = tab.icon
          const cls = [
            'flex flex-col items-center justify-center gap-1 flex-1 py-3 text-xs font-medium transition-colors',
            tab.active ? 'text-brand' : 'text-ink-3',
            tab.disabled ? 'opacity-40 cursor-not-allowed pointer-events-none' : '',
          ].join(' ')

          if (tab.disabled) {
            return (
              <span key={tab.label} className={cls} aria-disabled="true">
                <Icon active={tab.active} />
                <span>{tab.label}</span>
              </span>
            )
          }

          return (
            <Link key={tab.label} href={tab.href} className={cls}>
              <Icon active={tab.active} />
              <span>{tab.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
