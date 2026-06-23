/**
 * Next.js middleware — locale detection and redirect.
 *
 * Responsibilities:
 *   1. If the request path already starts with a valid locale (/fa, /en, /ar),
 *      write NEXT_LOCALE cookie (for root layout SSR) and continue.
 *   2. Otherwise, redirect to /{locale}{rest-of-path} where locale is:
 *        - the cookie value, but ONLY if NEXT_LOCALE_SRC=manual (explicit user pick)
 *        - 'fa' in all other cases (no Accept-Language fallback)
 *
 * The two-cookie design prevents a stale automatic NEXT_LOCALE=en cookie
 * (written when a user once visited /en) from hijacking the Persian default
 * on a fresh visit to the root domain.
 */
import { NextRequest, NextResponse } from 'next/server'
import {
  SUPPORTED_LOCALES,
  DEFAULT_LOCALE,
  LOCALE_COOKIE,
  LOCALE_SRC_COOKIE,
  LOCALE_SRC_MANUAL,
  isValidLocale,
  type Locale,
} from '@/lib/i18n'

/** Detect the best locale for this request — only trusts an explicit user selection. */
function detectLocale(request: NextRequest): Locale {
  // Only use the persisted locale if the user explicitly selected it
  const src = request.cookies.get(LOCALE_SRC_COOKIE)?.value
  if (src === LOCALE_SRC_MANUAL) {
    const cookieLocale = request.cookies.get(LOCALE_COOKIE)?.value
    if (cookieLocale && isValidLocale(cookieLocale)) return cookieLocale
  }
  // Persian is the unconditional hard default — never fall back to Accept-Language
  return DEFAULT_LOCALE
}

export function middleware(request: NextRequest): NextResponse {
  const { pathname } = request.nextUrl

  // Find whether the pathname already begins with a valid locale segment
  const pathnameLocale = SUPPORTED_LOCALES.find(
    (locale) => pathname === `/${locale}` || pathname.startsWith(`/${locale}/`),
  )

  if (pathnameLocale) {
    // Valid locale already in URL — refresh NEXT_LOCALE for root layout SSR.
    // Do NOT write NEXT_LOCALE_SRC here: visiting /en directly is not a manual selection.
    const response = NextResponse.next()
    response.cookies.set(LOCALE_COOKIE, pathnameLocale, {
      path: '/',
      maxAge: 60 * 60 * 24 * 365, // 1 year
      sameSite: 'lax',
      httpOnly: false, // readable by JS for cookie updates without reload
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
    '/((?!_next/static|_next/image|favicon\\.ico|icons|manifest\\.json|sw\\.js|offline\\.html|assets).*)',
  ],
}
