'use client'

import { useEffect } from 'react'
import { getDirection } from '@/lib/direction'
import type { Locale } from '@/lib/i18n'

/**
 * Keeps <html lang dir> in sync with the active locale during client-side navigation.
 * The root layout sets these attributes on the initial SSR render via the NEXT_LOCALE
 * cookie, but router.push() does not re-run the root layout. This component patches
 * the attributes on every locale change so direction flips without a full reload.
 */
export default function DirectionSync({ locale }: { locale: Locale }) {
  useEffect(() => {
    document.documentElement.lang = locale
    document.documentElement.dir = getDirection(locale)
  }, [locale])
  return null
}
