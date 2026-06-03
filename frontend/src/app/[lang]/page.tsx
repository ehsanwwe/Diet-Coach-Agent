import { notFound } from 'next/navigation'
import { isValidLocale, getDictionary, SUPPORTED_LOCALES, type Locale } from '@/lib/i18n'

type Props = {
  params: Promise<{ lang: string }>
}

/** Leaf/sprout icon — inline SVG, uses currentColor for the brand color. */
function AppIcon() {
  return (
    <svg
      width="44"
      height="44"
      viewBox="0 0 44 44"
      fill="none"
      aria-hidden="true"
      role="img"
    >
      {/* Stem */}
      <line
        x1="22"
        y1="40"
        x2="22"
        y2="22"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
      />
      {/* Right leaf */}
      <path
        d="M22 22 C22 22 36 18 36 8 C36 8 24 7 22 22"
        fill="currentColor"
        opacity="0.9"
      />
      {/* Left leaf */}
      <path
        d="M22 30 C22 30 10 27 10 17 C10 17 20 18 22 30"
        fill="currentColor"
        opacity="0.65"
      />
    </svg>
  )
}

/**
 * Splash / landing page for each locale.
 * App-like layout: centered on mobile, max 430px on desktop.
 * No auth, no features — establishes i18n, direction, and visual style.
 */
export default async function SplashPage({ params }: Props) {
  const { lang } = await params

  if (!isValidLocale(lang)) notFound()

  const locale = lang as Locale
  const dict = await getDictionary(locale)

  return (
    <div className="min-h-dvh bg-surface flex flex-col">
      {/* Mobile app container — centered on desktop */}
      <div className="app-container flex-1 flex flex-col items-center justify-center px-8 py-16 text-center">

        {/* App icon */}
        <div className="w-20 h-20 rounded-full bg-brand-muted flex items-center justify-center mb-8 text-brand">
          <AppIcon />
        </div>

        {/* App name */}
        <h1 className="text-3xl font-bold text-ink mb-3 leading-tight">
          {dict.common.appName}
        </h1>

        {/* Tagline */}
        <p className="text-base font-medium text-brand mb-4">
          {dict.splash.tagline}
        </p>

        {/* Description */}
        <p className="text-sm text-ink-2 leading-relaxed max-w-[300px] mb-12">
          {dict.splash.description}
        </p>

        {/* CTA */}
        <div className="flex flex-col items-center gap-3 w-full max-w-[280px]">
          <a
            href={`/${locale}/login`}
            className="w-full text-center py-4 rounded-2xl bg-brand text-elevated font-semibold text-sm"
          >
            {dict.splash.getStarted}
          </a>
          <a
            href={`/${locale}/dashboard`}
            className="w-full text-center py-3 rounded-2xl border border-line text-ink-2 text-sm font-medium"
          >
            {dict.nav.home}
          </a>
        </div>
      </div>

      {/* Language switcher — bottom of screen */}
      <div className="app-container pb-safe pb-8 flex justify-center items-center gap-6">
        {SUPPORTED_LOCALES.map((loc) => (
          <a
            key={loc}
            href={`/${loc}`}
            className={[
              'text-sm transition-colors',
              loc === locale
                ? 'text-brand font-semibold'
                : 'text-ink-3 hover:text-ink-2',
            ].join(' ')}
            aria-current={loc === locale ? 'page' : undefined}
            aria-label={dict.language[loc]}
          >
            {dict.language[loc]}
          </a>
        ))}
      </div>
    </div>
  )
}
