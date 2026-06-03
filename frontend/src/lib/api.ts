/**
 * Typed API client wrapping fetch.
 * Reads base URL from NEXT_PUBLIC_API_BASE_URL.
 * All requests include JSON content-type; auth token attached when available.
 */

import type { ApiError, ApiSuccess } from '@/types/auth'
import { getToken } from './storage'

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export class ApiRequestError extends Error {
  constructor(
    public readonly status: number,
    public readonly message: string,
    public readonly detail: Record<string, unknown> = {},
  ) {
    super(message)
    this.name = 'ApiRequestError'
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { auth?: boolean } = {},
): Promise<T> {
  const { auth = false, ...init } = options

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(init.headers as Record<string, string>),
  }

  if (auth) {
    const token = getToken()
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...init, headers })

  if (!res.ok) {
    let errorBody: ApiError = {
      status: 'error',
      message: 'Request failed',
      detail: {},
    }
    try {
      errorBody = await res.json()
    } catch {
      // non-JSON error body
    }
    const message =
      typeof errorBody.message === 'string' && errorBody.message
        ? errorBody.message
        : 'Request failed'
    throw new ApiRequestError(res.status, message, errorBody.detail ?? {})
  }

  return res.json() as Promise<T>
}

export const api = {
  post: <T>(path: string, body: unknown, auth = false) =>
    request<ApiSuccess<T>>(path, {
      method: 'POST',
      body: JSON.stringify(body),
      auth,
    }),

  get: <T>(path: string, auth = false) =>
    request<ApiSuccess<T>>(path, { method: 'GET', auth }),
}
