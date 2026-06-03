/**
 * Auth API helpers. All auth-related API calls go through here.
 * Components and hooks import from this file, not from api.ts directly.
 */

import type { AuthUser, TokenResponse } from '@/types/auth'
import { api } from './api'
import { clearToken, setStoredUser, setToken } from './storage'

export async function requestOtp(phoneNumber: string): Promise<void> {
  await api.post('/api/v1/auth/request-otp', { phone_number: phoneNumber })
}

export async function verifyOtp(
  phoneNumber: string,
  otpCode: string,
): Promise<TokenResponse> {
  const res = await api.post<TokenResponse>('/api/v1/auth/verify-otp', {
    phone_number: phoneNumber,
    otp_code: otpCode,
  })
  const tokenData = res.data
  setToken(tokenData.access_token)
  setStoredUser<AuthUser>(tokenData.user)
  return tokenData
}

export async function logout(): Promise<void> {
  try {
    await api.post('/api/v1/auth/logout', {}, true)
  } finally {
    clearToken()
  }
}

export async function getCurrentUser(): Promise<AuthUser> {
  const res = await api.get<AuthUser>('/api/v1/auth/me', true)
  return res.data
}
