import { notFound } from 'next/navigation'
import { isValidLocale, getDictionary, type Locale } from '@/lib/i18n'
import SplashOrRedirect from '@/components/SplashOrRedirect'

type Props = {
  params: Promise<{ lang: string }>
}

/**
 * Home route for each locale.
 * Authenticated users are redirected to /[lang]/dashboard by SplashOrRedirect.
 * Unauthenticated users see the splash / marketing page.
 */
export default async function HomePage({ params }: Props) {
  const { lang } = await params
  if (!isValidLocale(lang)) notFound()
  const locale = lang as Locale
  const dict = await getDictionary(locale)
  return <SplashOrRedirect dict={dict} locale={locale} />
}
