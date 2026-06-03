import { notFound, redirect } from 'next/navigation'
import { getDictionary, isValidLocale, type Locale } from '@/lib/i18n'
import OtpVerifyForm from '@/components/auth/OtpVerifyForm'

type Props = {
  params: Promise<{ lang: string }>
  searchParams: Promise<{ phone?: string }>
}

export default async function OtpVerifyPage({ params, searchParams }: Props) {
  const { lang } = await params
  if (!isValidLocale(lang)) notFound()

  const locale = lang as Locale
  const { phone } = await searchParams
  if (!phone) redirect(`/${locale}/login`)

  const dict = await getDictionary(locale)

  const decodedPhone = decodeURIComponent(phone)

  return (
    <div className="min-h-dvh bg-surface flex flex-col">
      <div className="app-container flex-1 flex flex-col justify-center px-8 py-16">

        {/* Header */}
        <div className="mb-10 text-start">
          <h1 className="text-2xl font-bold text-ink mb-2">
            {dict.auth.otpTitle}
          </h1>
          <p className="text-sm text-ink-2">
            {dict.auth.otpSubtitle}
          </p>
          <p className="text-sm font-medium text-brand mt-1" dir="ltr">
            {decodedPhone}
          </p>
        </div>

        <OtpVerifyForm
          dict={{ ...dict.auth, loading: dict.common.loading }}
          locale={locale}
          phone={decodedPhone}
        />

        {/* Back link */}
        <div className="mt-6 text-center">
          <a
            href={`/${locale}/login`}
            className="text-sm text-ink-3 hover:text-ink-2 transition-colors"
          >
            {dict.common.back}
          </a>
        </div>
      </div>
    </div>
  )
}
