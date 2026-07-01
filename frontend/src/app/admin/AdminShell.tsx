'use client'

/**
 * AdminShell: wraps every protected admin page.
 * Checks for admin token; redirects to login if missing.
 * Renders sidebar + main content area.
 */

import { useEffect, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { getAdminToken, clearAdminToken } from '@/lib/admin-storage'
import { adminApi, AdminApiError } from '@/lib/admin-api'

export default function AdminShell({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()
  const [verified, setVerified] = useState(false)

  useEffect(() => {
    const token = getAdminToken()
    if (!token) {
      router.replace('/admin/login')
      return
    }
    adminApi.me().then(() => {
      setVerified(true)
    }).catch((err: unknown) => {
      if (err instanceof AdminApiError && err.status === 401) {
        clearAdminToken()
        router.replace('/admin/login')
      } else {
        // Network error — allow access (backend will re-validate each request)
        setVerified(true)
      }
    })
  }, [router])

  const handleLogout = async () => {
    try {
      await adminApi.logout()
    } catch {
      // ignore
    }
    clearAdminToken()
    router.replace('/admin/login')
  }

  if (!verified) {
    return (
      <div className="min-h-screen flex items-center justify-center text-stone-400 text-sm">
        در حال بارگذاری...
      </div>
    )
  }

  const navItems = [
    { href: '/admin/users', label: 'مدیریت کاربران' },
  ]

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-52 bg-white border-l border-stone-100 flex flex-col">
        <div className="px-5 py-5 border-b border-stone-100">
          <p className="text-sm font-semibold text-stone-700">داشبورد ادمین</p>
          <p className="text-xs text-stone-400 mt-0.5">مربی تغذیه</p>
        </div>

        <nav className="flex-1 p-3 space-y-1">
          {navItems.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`block px-3 py-2 rounded-xl text-sm transition-colors ${
                pathname?.startsWith(item.href)
                  ? 'bg-stone-100 text-stone-800 font-medium'
                  : 'text-stone-500 hover:bg-stone-50 hover:text-stone-700'
              }`}
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="p-3 border-t border-stone-100">
          <button
            onClick={handleLogout}
            className="w-full px-3 py-2 text-sm text-stone-500 hover:text-red-500
                       hover:bg-red-50 rounded-xl transition-colors text-right"
          >
            خروج
          </button>
        </div>
      </aside>

      {/* Main content */}
      <main className="flex-1 p-6 overflow-auto">
        {children}
      </main>
    </div>
  )
}
