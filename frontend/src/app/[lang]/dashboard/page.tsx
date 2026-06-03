import { notFound } from 'next/navigation'
import { getDictionary, isValidLocale, type Locale } from '@/lib/i18n'
import AuthGuard from '@/components/auth/AuthGuard'
import AppBottomNav from '@/components/layout/AppBottomNav'
import NutritionDashboard from '@/components/nutrition/NutritionDashboard'

type Props = { params: Promise<{ lang: string }> }

export default async function DashboardPage({ params }: Props) {
  const { lang } = await params
  if (!isValidLocale(lang)) notFound()
  const locale = lang as Locale
  const dict = await getDictionary(locale)

  return (
    <AuthGuard locale={locale}>
      <div className="app-container">
        <NutritionDashboard dict={dict} locale={locale} />
        <AppBottomNav locale={locale} dict={dict} />
      </div>
    </AuthGuard>
  )
}
