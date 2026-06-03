import type { Metadata } from 'next'
import { notFound } from 'next/navigation'
import { isValidLocale, getDictionary, type Locale } from '@/lib/i18n'

type Props = {
  children: React.ReactNode
  params: Promise<{ lang: string }>
}

/** Generate static routes for all supported locales. */
export async function generateStaticParams() {
  return [{ lang: 'fa' }, { lang: 'en' }, { lang: 'ar' }]
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { lang } = await params
  if (!isValidLocale(lang)) return {}

  const dict = await getDictionary(lang as Locale)
  return {
    title: dict.common.appName,
    description: dict.splash.description,
  }
}

/**
 * Locale-segment layout.
 * Validates the lang param and 404s on unknown locales.
 * The dictionary is available in children via getDictionary() in each page.
 */
export default async function LangLayout({ children, params }: Props) {
  const { lang } = await params

  if (!isValidLocale(lang)) {
    notFound()
  }

  return <>{children}</>
}
