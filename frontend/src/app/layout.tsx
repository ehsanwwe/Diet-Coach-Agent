import type { Metadata, Viewport } from 'next'
import { cookies } from 'next/headers'
import './globals.css'
import { DEFAULT_LOCALE, LOCALE_COOKIE, isValidLocale } from '@/lib/i18n'
import { getDirection } from '@/lib/direction'
import { ServiceWorkerRegistration } from '@/components/service-worker'

export const metadata: Metadata = {
  title: {
    default: 'مربی تغذیه | Diet Coach',
    template: '%s | مربی تغذیه',
  },
  description: 'مربی هوشمند تغذیه شما — راهنمای روزانه سلامت و تغذیه شخصی‌سازی‌شده',
  manifest: '/manifest.json',
  appleWebApp: {
    capable: true,
    statusBarStyle: 'default',
    title: 'مربی تغذیه',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  userScalable: false,
  themeColor: '#567A58',
}

/**
 * Root layout — sets <html lang dir> from the NEXT_LOCALE cookie written by middleware.
 * This is a dynamic Server Component (reads cookies per-request) so direction is
 * applied server-side with zero client-side flicker.
 */
export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  const cookieStore = await cookies()
  const cookieLocale = cookieStore.get(LOCALE_COOKIE)?.value
  const locale =
    cookieLocale && isValidLocale(cookieLocale) ? cookieLocale : DEFAULT_LOCALE
  const dir = getDirection(locale)

  return (
    <html lang={locale} dir={dir}>
      <body>
        <ServiceWorkerRegistration />
        {children}
      </body>
    </html>
  )
}
