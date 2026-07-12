'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import AppIcon, { type AppIconName } from '@/components/ui/AppIcon'

interface Props {
  locale: Locale
  dict: Pick<Dictionary, 'nav'>
}

type NavTab = {
  href: string
  label: string
  icon: AppIconName
  active: boolean
  disabled: boolean
}

export default function AppBottomNav({ locale, dict }: Props) {
  const pathname = usePathname()

  const isActive = (segment: string) => pathname.includes(`/${segment}`)

  const tabs: NavTab[] = [
    {
      href: `/${locale}/settings`,
      label: dict.nav.settings,
      icon: 'settings',
      active: isActive('settings'),
      disabled: false,
    },
    {
      href: `/${locale}/chat`,
      label: dict.nav.chat,
      icon: 'chat',
      active: isActive('chat'),
      disabled: false,
    },
    {
      href: `/${locale}/progress`,
      label: dict.nav.progress,
      icon: 'progress',
      active: isActive('progress'),
      disabled: false,
    },
    {
      href: `/${locale}/nutrition/plan`,
      label: dict.nav.plan,
      icon: 'calendar',
      active: pathname.includes('/nutrition/plan'),
      disabled: false,
    },
    {
      href: `/${locale}/dashboard`,
      label: dict.nav.home,
      icon: 'home',
      active: isActive('dashboard') || pathname === `/${locale}`,
      disabled: false,
    },
  ]

  return (
    <nav className="fixed bottom-0 left-1/2 z-50 w-full max-w-[var(--app-max-width)] -translate-x-1/2 pb-safe bg-elevated border-t border-line">
      <div className="w-full flex flex-row items-stretch" dir="ltr">
        {tabs.map((tab) => {
          const cls = [
            'flex flex-col items-center justify-center gap-1 flex-1 py-3 text-xs font-medium transition-colors',
            tab.active ? 'text-brand' : 'text-ink-3',
            tab.disabled ? 'opacity-40 cursor-not-allowed pointer-events-none' : '',
          ].join(' ')

          if (tab.disabled) {
            return (
              <span key={tab.label} className={cls} aria-disabled="true">
                <AppIcon name={tab.icon} size={22} strokeWidth={tab.active ? 2.2 : 1.8} />
                <span dir="auto">{tab.label}</span>
              </span>
            )
          }

          return (
            <Link key={tab.label} href={tab.href} className={cls}>
              <AppIcon name={tab.icon} size={22} strokeWidth={tab.active ? 2.2 : 1.8} />
              <span dir="auto">{tab.label}</span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
