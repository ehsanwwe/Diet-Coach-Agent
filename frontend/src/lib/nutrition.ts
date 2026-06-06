import { getToken } from './storage'
import type {
  CalendarResponse,
  GenerateWeekResponse,
  MealAnalysisResponse,
  MealAnalyzeRequest,
  NutritionPlanResponse,
  NutritionProfileResponse,
  WhatToEatNowRequest,
  WhatToEatNowResponse,
} from '@/types/nutrition'

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
const BASE = '/api/v1/nutrition'

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) {
    throw new Error('UNAUTHORIZED')
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(err?.detail?.message ?? err?.message ?? 'Request failed')
  }
  return res.json() as Promise<T>
}

export async function getNutritionProfile(): Promise<NutritionProfileResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/profile`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<NutritionProfileResponse>(res)
}

export async function getNutritionPlan(): Promise<NutritionPlanResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/plan`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<NutritionPlanResponse>(res)
}

export async function generateNutritionPlan(): Promise<NutritionPlanResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/plan/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
  })
  return handleResponse<NutritionPlanResponse>(res)
}

export async function analyzeMeal(
  body: MealAnalyzeRequest,
): Promise<MealAnalysisResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/meal/analyze`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  })
  return handleResponse<MealAnalysisResponse>(res)
}

export async function whatToEatNow(
  body: WhatToEatNowRequest,
): Promise<WhatToEatNowResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/what-to-eat-now`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  })
  return handleResponse<WhatToEatNowResponse>(res)
}

export async function getMealPlanCalendar(params?: {
  start_date?: string
  days?: number
  locale?: string
}): Promise<CalendarResponse> {
  const qs = new URLSearchParams()
  if (params?.start_date) qs.set('start_date', params.start_date)
  if (params?.days != null) qs.set('days', String(params.days))
  if (params?.locale) qs.set('locale', params.locale)
  const query = qs.toString() ? `?${qs.toString()}` : ''
  const res = await fetch(`${BASE_URL}${BASE}/calendar${query}`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<CalendarResponse>(res)
}

export async function generateMealPlanWeek(params?: {
  start_date?: string
  locale?: string
  force?: boolean
}): Promise<GenerateWeekResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/calendar/generate-week`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({
      start_date: params?.start_date ?? null,
      locale: params?.locale ?? null,
      force: params?.force ?? false,
    }),
  })
  return handleResponse<GenerateWeekResponse>(res)
}

export async function regenerateMealPlanDay(params: {
  plan_date: string
  locale?: string
}): Promise<{ locale: string; plan_date: string; day: import('@/types/nutrition').PlanDay }> {
  const res = await fetch(`${BASE_URL}${BASE}/calendar/regenerate-day`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ plan_date: params.plan_date, locale: params.locale ?? null }),
  })
  return handleResponse(res)
}
