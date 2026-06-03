/**
 * Next.js middleware — locale detection and redirect.
 *
 * Responsibilities:
 *   1. If the request path already starts with a valid locale (/fa, /en, /ar),
 *      update the NEXT_LOCALE cookie and continue.
 *   2. Otherwise, detect the preferred locale from cookie → Accept-Language → default (fa),
 *      then redirect to /{locale}{rest-of-path}.
 *
 * The cookie NEXT_LOCALE is read by app/layout.tsx to set <html lang dir> server-side
 * with zero client-side flicker.
 */
import { NextRequest, NextResponse } from 'next/server'
import {
  SUPPORTED_LOCALES,
  DEFAULT_LOCALE,
  LOCALE_COOKIE,
  isValidLocale,
  type Locale,
} from '@/lib/i18n'

/** Parse Accept-Language header into an ordered list of language codes. */
function parseAcceptLanguage(header: string): string[] {
  return header
    .split(',')
    .map((entry) => {
      const [lang, q] = entry.trim().split(';q=')
      return { lang: lang.trim().split('-')[0].toLowerCase(), q: q ? parseFloat(q) : 1 }
    })
    .sort((a, b) => b.q - a.q)
    .map((e) => e.lang)
    .filter(Boolean)
}

/** Detect the best locale for this request. */
function detectLocale(request: NextRequest): Locale {
  // 1. Prefer the persisted cookie
  const cookieLocale = request.cookies.get(LOCALE_COOKIE)?.value
  if (cookieLocale && isValidLocale(cookieLocale)) return cookieLocale

  // 2. Accept-Language header
  const acceptLang = request.headers.get('Accept-Language') ?? ''
  for (const lang of parseAcceptLanguage(acceptLang)) {
    if (isValidLocale(lang)) return lang
  }

  return DEFAULT_LOCALE
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl

  // Find whether the pathname already begins with a valid locale segment
  const pathnameLocale = SUPPORTED_LOCALES.find(
    (locale) => pathname === `/${locale}` || pathname.startsWith(`/${locale}/`),
  )

  if (pathnameLocale) {
    // Valid locale already in URL — refresh the cookie and continue
    const response = NextResponse.next()
    response.cookies.set(LOCALE_COOKIE, pathnameLocale, {
      path: '/',
      maxAge: 60 * 60 * 24 * 365, // 1 year
      sameSite: 'lax',
      httpOnly: false, // needs to be readable by JS for locale switching without reload
    })
    return response
  }

  // No valid locale in URL — detect and redirect
  const locale = detectLocale(request)
  const target = new URL(
    `/${locale}${pathname === '/' ? '' : pathname}`,
    request.url,
  )
  target.search = request.nextUrl.search

  const response = NextResponse.redirect(target)
  response.cookies.set(LOCALE_COOKIE, locale, {
    path: '/',
    maxAge: 60 * 60 * 24 * 365,
    sameSite: 'lax',
    httpOnly: false,
  })
  return response
}

export const config = {
  // Run middleware on all routes except Next.js internals and static public files
  matcher: [
    '/((?!_next/static|_next/image|favicon\\.ico|icons|manifest\\.json|sw\\.js|offline\\.html).*)',
  ],
}
