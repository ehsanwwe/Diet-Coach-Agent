/**
 * i18n types, constants, and dictionary loader.
 *
 * Dictionary type is defined in dictionaries/fa.ts (source of truth).
 * All locale detection happens server-side in middleware.ts.
 * getDictionary() is safe to call in any Server Component.
 */
import type { Dictionary } from '@/dictionaries/fa'

export type { Dictionary }

export const SUPPORTED_LOCALES = ['fa', 'en', 'ar'] as const
export type Locale = (typeof SUPPORTED_LOCALES)[number]

export const DEFAULT_LOCALE: Locale = 'fa'

/** RTL locales: fa (Persian) and ar (Arabic) */
export const RTL_LOCALES: readonly Locale[] = ['fa', 'ar'] as const

export const LOCALE_COOKIE = 'NEXT_LOCALE'

export function isValidLocale(value: string): value is Locale {
  return (SUPPORTED_LOCALES as readonly string[]).includes(value)
}

/** Load the dictionary for a given locale. Server Component only. */
export async function getDictionary(locale: Locale): Promise<Dictionary> {
  switch (locale) {
    case 'en':
      return (await import('@/dictionaries/en')).default
    case 'ar':
      return (await import('@/dictionaries/ar')).default
    default:
      return (await import('@/dictionaries/fa')).default
  }
}
