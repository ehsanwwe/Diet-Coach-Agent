/**
 * Direction utilities for RTL/LTR layout support.
 *
 * All helpers are pure functions — safe to call from any Server or Client Component.
 * The `dir` attribute is set on <html> in root layout.tsx from the locale cookie.
 *
 * Conventions:
 *   - Never use physical CSS props (left/right); use logical (inline-start/inline-end).
 *   - Never use pl-/pr-/ml-/mr- Tailwind classes; use ps-/pe-/ms-/me-.
 *   - For directional icons, apply getIconFlipClass() to mirror in RTL.
 *   - For Framer Motion slide animations, use getSlideX() for the entry x offset.
 */
import { RTL_LOCALES, type Locale } from '@/lib/i18n'

export type Direction = 'rtl' | 'ltr'

/** Returns 'rtl' for Persian and Arabic, 'ltr' for everything else. */
export function getDirection(locale: Locale): Direction {
  return (RTL_LOCALES as readonly string[]).includes(locale) ? 'rtl' : 'ltr'
}

/** True when the locale uses a right-to-left script. */
export function isRTL(locale: Locale): boolean {
  return getDirection(locale) === 'rtl'
}

/**
 * Framer Motion x-offset for "next step" slide direction.
 *   RTL forward: content enters from the right (+100)
 *   LTR forward: content enters from the left  (-100)
 *   Backward: negated.
 */
export function getSlideX(locale: Locale, direction: 'forward' | 'backward'): number {
  const rtl = isRTL(locale)
  if (direction === 'forward') return rtl ? 100 : -100
  return rtl ? -100 : 100
}

/**
 * Tailwind class to mirror a "forward-pointing" directional icon in RTL.
 * Apply to <ChevronRight />, <ArrowRight />, etc.
 *
 *   LTR: → (no flip needed)
 *   RTL: ← (scaleX(-1) applied)
 *
 * Usage:  <ChevronRight className={getIconFlipClass(locale)} />
 */
export function getIconFlipClass(locale: Locale): string {
  return isRTL(locale) ? '-scale-x-100' : ''
}

/**
 * CSS transform object for icon flipping — for use with inline style prop.
 * Returns an empty object in LTR so spreading is always safe.
 */
export function getIconFlipStyle(locale: Locale): { transform?: string } {
  return isRTL(locale) ? { transform: 'scaleX(-1)' } : {}
}
