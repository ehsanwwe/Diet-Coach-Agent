'use client'

import { useCallback, useEffect, useState } from 'react'
import type { AuthUser } from '@/types/auth'
import { getCurrentUser, logout as authLogout } from '@/lib/auth'
import { clearToken, getStoredUser, getToken } from '@/lib/storage'

interface AuthState {
  user: AuthUser | null
  isLoading: boolean
  isAuthenticated: boolean
}

export function useAuth() {
  const [state, setState] = useState<AuthState>({
    user: null,
    isLoading: true,
    isAuthenticated: false,
  })

  useEffect(() => {
    const token = getToken()
    if (!token) {
      setState({ user: null, isLoading: false, isAuthenticated: false })
      return
    }

    // Optimistically show cached user while verifying
    const cached = getStoredUser<AuthUser>()
    if (cached) {
      setState({ user: cached, isLoading: false, isAuthenticated: true })
    }

    // Verify token is still valid with the server
    getCurrentUser()
      .then((user) => {
        setState({ user, isLoading: false, isAuthenticated: true })
      })
      .catch(() => {
        clearToken()
        setState({ user: null, isLoading: false, isAuthenticated: false })
      })
  }, [])

  const logout = useCallback(async () => {
    await authLogout()
    setState({ user: null, isLoading: false, isAuthenticated: false })
  }, [])

  return { ...state, logout }
}
