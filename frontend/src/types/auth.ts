export interface AuthUser {
  id: string
  phone: string
  is_active: boolean
  is_onboarded: boolean
  created_at: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_at: string
  user: AuthUser
}

export interface ApiSuccess<T> {
  status: 'ok'
  data: T
}

export interface ApiError {
  status: 'error'
  message: string
  detail: Record<string, unknown>
}
