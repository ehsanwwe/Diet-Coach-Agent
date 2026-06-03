'use client'

import { useCallback, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import type { NutritionProfileResponse } from '@/types/nutrition'
import { getNutritionProfile } from '@/lib/nutrition'
import type { Locale } from '@/lib/i18n'

interface State {
  profile: NutritionProfileResponse | null
  isLoading: boolean
  error: string | null
}

export function useNutritionProfile(locale: Locale) {
  const router = useRouter()
  const [state, setState] = useState<State>({
    profile: null,
    isLoading: true,
    error: null,
  })

  const fetch = useCallback(async () => {
    setState((s) => ({ ...s, isLoading: true, error: null }))
    try {
      const profile = await getNutritionProfile()
      setState({ profile, isLoading: false, error: null })
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Unknown error'
      if (msg === 'UNAUTHORIZED') {
        router.replace(`/${locale}/login`)
        return
      }
      setState((s) => ({ ...s, isLoading: false, error: msg }))
    }
  }, [locale, router])

  useEffect(() => {
    fetch()
  }, [fetch])

  return { ...state, refetch: fetch }
}
