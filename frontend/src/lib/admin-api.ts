/**
 * Typed API client for admin panel endpoints.
 * Sends X-Admin-Token header — never touches normal user auth token.
 */

import { getAdminToken } from './admin-storage'

const BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'

export class AdminApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly message: string,
  ) {
    super(message)
    this.name = 'AdminApiError'
  }
}

async function adminRequest<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const token = getAdminToken()
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  }
  if (token) {
    headers['X-Admin-Token'] = token
  }

  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (!res.ok) {
    let message = 'Request failed'
    try {
      const body = await res.json()
      if (body?.detail?.message) message = body.detail.message
      else if (typeof body?.message === 'string') message = body.message
    } catch {
      // non-JSON body
    }
    throw new AdminApiError(res.status, message)
  }

  return res.json() as Promise<T>
}

// ── Types ─────────────────────────────────────────────────────────────────────

export interface AdminTokenResponse {
  admin_token: string
  expires_at: string
}

export interface AdminUserListItem {
  id: string
  phone: string
  full_name: string | null
  language: string | null
  is_onboarded: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  has_nutrition_plan: boolean
  chat_message_count: number
  latest_activity: string | null
}

export interface AdminUserDetail {
  id: string
  phone: string
  is_active: boolean
  is_onboarded: boolean
  created_at: string
  updated_at: string
  full_name: string | null
  gender: string | null
  birth_date: string | null
  height_cm: number | null
  weight_kg: number | null
  target_weight_kg: number | null
  language: string | null
  goal_type: string | null
  risk_level: string | null
  chat_session_count: number
  chat_message_count: number
  nutrition_plan_count: number
}

export interface AdminDeleteResponse {
  deleted: boolean
  user_id: string
  deleted_records: Record<string, number>
}

// ── API functions ─────────────────────────────────────────────────────────────

export const adminApi = {
  login: async (username: string, password: string): Promise<AdminTokenResponse> => {
    const res = await adminRequest<{ data: AdminTokenResponse }>('/api/v1/admin/auth/login', {
      method: 'POST',
      body: JSON.stringify({ username, password }),
    })
    return res.data
  },

  logout: async (): Promise<void> => {
    await adminRequest('/api/v1/admin/auth/logout', { method: 'POST' })
  },

  me: async (): Promise<{ username: string }> => {
    const res = await adminRequest<{ data: { username: string } }>('/api/v1/admin/auth/me')
    return res.data
  },

  listUsers: async (): Promise<AdminUserListItem[]> => {
    const res = await adminRequest<{ data: AdminUserListItem[] }>('/api/v1/admin/users')
    return res.data
  },

  getUser: async (userId: string): Promise<AdminUserDetail> => {
    const res = await adminRequest<{ data: AdminUserDetail }>(`/api/v1/admin/users/${userId}`)
    return res.data
  },

  exportUser: (userId: string, type: 'onboarding' | 'chat' | 'nutrition' | 'all'): string => {
    // Returns a URL; caller fetches with X-Admin-Token attached via downloadExport()
    return `${BASE_URL}/api/v1/admin/users/${userId}/export/${type}`
  },

  downloadExport: async (userId: string, type: 'onboarding' | 'chat' | 'nutrition' | 'all'): Promise<void> => {
    const token = getAdminToken()
    const res = await fetch(
      `${BASE_URL}/api/v1/admin/users/${userId}/export/${type}`,
      { headers: { 'X-Admin-Token': token ?? '' } },
    )
    if (!res.ok) throw new AdminApiError(res.status, 'Export failed')
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `user-${userId}-${type}-export.json`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  },

  deleteUser: async (userId: string): Promise<AdminDeleteResponse> => {
    const res = await adminRequest<{ data: AdminDeleteResponse }>(
      `/api/v1/admin/users/${userId}`,
      { method: 'DELETE' },
    )
    return res.data
  },
}
