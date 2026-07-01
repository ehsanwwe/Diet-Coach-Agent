/**
 * Admin panel root layout.
 * RTL, Persian-only, completely separate from user-facing locale layouts.
 * No bottom nav, no locale routing.
 */
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'ادمین | مربی تغذیه',
  robots: 'noindex, nofollow',
}

export default function AdminRootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="fa" dir="rtl">
      <body className="bg-stone-50 text-stone-800 min-h-screen">
        {children}
      </body>
    </html>
  )
}
