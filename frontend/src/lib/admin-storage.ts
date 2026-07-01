'use client'

/**
 * Admin token storage — completely separate from normal user token.
 * Uses a different localStorage key so admin login never overwrites user session.
 */

const ADMIN_TOKEN_KEY = 'diet_coach_admin_token'

export function getAdminToken(): string | null {
  if (typeof window === 'undefined') return null
  return localStorage.getItem(ADMIN_TOKEN_KEY)
}

export function setAdminToken(token: string): void {
  if (typeof window === 'undefined') return
  localStorage.setItem(ADMIN_TOKEN_KEY, token)
}

export function clearAdminToken(): void {
  if (typeof window === 'undefined') return
  localStorage.removeItem(ADMIN_TOKEN_KEY)
}
