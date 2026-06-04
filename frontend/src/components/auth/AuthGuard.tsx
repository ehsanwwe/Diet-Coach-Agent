'use client'

import { useEffect, useRef } from 'react'
import { useRouter, usePathname } from 'next/navigation'
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
  const pathname = usePathname()
  const routerRef = useRef(router)
  routerRef.current = router

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      const loginPath = `/${locale}/login`
      // Guard: never redirect to the same path we're already on
      if (pathname !== loginPath && !pathname.startsWith(`/${locale}/login/`)) {
        routerRef.current.replace(loginPath)
      }
    }
  }, [isLoading, isAuthenticated, locale, pathname])

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
