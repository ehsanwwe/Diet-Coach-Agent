import { notFound } from 'next/navigation'
import { getDictionary, isValidLocale, type Locale } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import ProgressScreen from '@/components/progress/ProgressScreen'

type Props = { params: Promise<{ lang: string }> }

export default async function ProgressPage({ params }: Props) {
  const { lang } = await params
  if (!isValidLocale(lang)) notFound()
  const locale = lang as Locale
  const dict = await getDictionary(locale)

  return (
    <AuthGuard locale={locale}>
      <div className="app-container">
        <ProgressScreen dict={dict} locale={locale} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
