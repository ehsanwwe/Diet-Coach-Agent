import { notFound } from 'next/navigation'
import { getDictionary, isValidLocale, type Locale } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import SettingsScreen from '@/components/settings/SettingsScreen'

type Props = { params: Promise<{ lang: string }> }

export default async function SettingsPage({ params }: Props) {
  const { lang } = await params
  if (!isValidLocale(lang)) notFound()
  const locale = lang as Locale
  const dict = await getDictionary(locale)

  return (
    <AuthGuard locale={locale}>
      <div className="app-container">
        <SettingsScreen locale={locale} dict={dict} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
