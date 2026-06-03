import { getToken } from './storage'
import type {
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
