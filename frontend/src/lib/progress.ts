import { getToken } from './storage'
import type {
  CheckInRequest,
  CheckInResponse,
  ProgressSummaryResponse,
  WeeklyReportResponse,
} from '@/types/progress'

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
const BASE = '/api/v1/progress'

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

export async function submitCheckIn(body: CheckInRequest): Promise<CheckInResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/check-in`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify(body),
  })
  return handleResponse<CheckInResponse>(res)
}

export async function getProgressSummary(): Promise<ProgressSummaryResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/summary`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<ProgressSummaryResponse>(res)
}

export async function getWeeklyReport(): Promise<WeeklyReportResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/weekly-report`, {
    headers: { ...authHeaders() },
  })
  return handleResponse<WeeklyReportResponse>(res)
}
