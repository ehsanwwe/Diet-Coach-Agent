import { notFound } from 'next/navigation'
import { getDictionary, isValidLocale, type Locale } from '@/lib/i18n'
import PhoneLoginForm from '@/components/auth/PhoneLoginForm'
import LocaleFlagSwitcher from '@/components/LocaleFlagSwitcher'

type Props = {
  params: Promise<{ lang: string }>
}

export default async function LoginPage({ params }: Props) {
  const { lang } = await params
  if (!isValidLocale(lang)) notFound()

  const locale = lang as Locale
  const dict = await getDictionary(locale)

  return (
    <div className="min-h-dvh bg-surface flex flex-col">
      <div className="app-container flex-1 flex flex-col justify-center px-8 py-16">

        {/* Header */}
        <div className="mb-10 text-start">
          <h1 className="text-2xl font-bold text-ink mb-2">
            {dict.auth.loginTitle}
          </h1>
          <p className="text-sm text-ink-2">
            {dict.auth.loginSubtitle}
          </p>
        </div>

        <PhoneLoginForm
          dict={{ ...dict.auth, loading: dict.common.loading }}
          locale={locale}
        />
      </div>

      {/* Language selector */}
      <div className="app-container pb-safe pb-8 flex flex-col items-center">
        <LocaleFlagSwitcher locale={locale} dict={dict} />
      </div>
    </div>
  )
}
