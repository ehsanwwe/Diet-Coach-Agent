'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import type { Locale } from '@/lib/i18n'
import { useAuth } from '@/hooks/useAuth'

interface Props {
  locale: Locale
  children: React.ReactNode
}

/**
 * Redirects unauthenticated users to the login page.
 * Wrap protected Client Component subtrees with this.
 */
export default function AuthGuard({ locale, children }: Props) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(`/${locale}/login`)
    }
  }, [isLoading, isAuthenticated, locale, router])

  if (isLoading) {
    return (
      <div className="min-h-dvh bg-surface flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin" />
      </div>
    )
  }

  if (!isAuthenticated) return null

  return <>{children}</>
}
