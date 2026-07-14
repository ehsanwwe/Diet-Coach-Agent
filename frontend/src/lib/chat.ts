import { getToken } from './storage'
import type { ApiSuccess } from '@/types/auth'
import type { ChatHistoryResponse, ChatMessageResponse } from '@/types/chat'
import { ApiRequestError } from './api'

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
const BASE = '/api/v1/chat'

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function handleResponse<T>(res: Response): Promise<T> {
  if (res.status === 401) throw new Error('UNAUTHORIZED')
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Request failed' }))
    const message = err?.detail?.message ?? err?.message ?? 'Request failed'
    throw new ApiRequestError(res.status, message, err?.detail?.detail ?? {})
  }
  return res.json() as Promise<T>
}

export async function editChatMessage(
  sessionId: string,
  messageId: string,
  content: string,
): Promise<ChatMessageResponse> {
  const res = await fetch(
    `${BASE_URL}${BASE}/sessions/${encodeURIComponent(sessionId)}/messages/${encodeURIComponent(messageId)}`,
    {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json', ...authHeaders() },
      body: JSON.stringify({ content }),
    },
  )
  const wrapped = await handleResponse<ApiSuccess<ChatMessageResponse>>(res)
  return wrapped.data
}

export async function sendChatMessage(
  message: string,
  clientMessageId?: string,
): Promise<ChatMessageResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/message`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ message, client_message_id: clientMessageId }),
  })
  const wrapped = await handleResponse<ApiSuccess<ChatMessageResponse>>(res)
  return wrapped.data
}

export async function getChatHistory(): Promise<ChatHistoryResponse> {
  const res = await fetch(`${BASE_URL}${BASE}/history`, {
    headers: { ...authHeaders() },
  })
  const wrapped = await handleResponse<ApiSuccess<ChatHistoryResponse>>(res)
  return wrapped.data
}

export async function clearChatMemory(): Promise<void> {
  const res = await fetch(`${BASE_URL}${BASE}/clear`, {
    method: 'POST',
    headers: { ...authHeaders() },
  })
  if (res.status === 401) throw new Error('UNAUTHORIZED')
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(err?.detail?.message ?? err?.message ?? 'Request failed')
  }
}
