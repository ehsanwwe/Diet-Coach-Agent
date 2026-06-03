import { getToken } from './storage'
import type { ApiSuccess } from '@/types/auth'
import type {
  AudioUploadResponse,
  ChatHistoryResponse,
  TextMessageResponse,
} from '@/types/onboardingChat'

const BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? 'http://localhost:8000'
const BASE = '/api/v1/onboarding'

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

export async function sendTextMessage(
  message: string,
): Promise<ApiSuccess<TextMessageResponse>> {
  const res = await fetch(`${BASE_URL}${BASE}/chat/text`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ message }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(err?.detail?.message ?? err?.message ?? 'Failed to send message')
  }
  return res.json()
}

export async function uploadAudio(
  blob: Blob,
  mimeType: string,
  durationSeconds?: number,
): Promise<ApiSuccess<AudioUploadResponse>> {
  const form = new FormData()
  form.append('file', blob, `recording${_ext(mimeType)}`)
  if (durationSeconds != null) {
    form.append('duration_seconds', String(durationSeconds))
  }

  const res = await fetch(`${BASE_URL}${BASE}/chat/audio`, {
    method: 'POST',
    headers: { ...authHeaders() },
    body: form,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Upload failed' }))
    throw new Error(err?.detail?.message ?? err?.message ?? 'Failed to upload audio')
  }
  return res.json()
}

export async function getChatHistory(): Promise<ApiSuccess<ChatHistoryResponse>> {
  const res = await fetch(`${BASE_URL}${BASE}/chat/history`, {
    method: 'GET',
    headers: { ...authHeaders() },
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: 'Request failed' }))
    throw new Error(err?.detail?.message ?? err?.message ?? 'Failed to load history')
  }
  return res.json()
}

function _ext(mime: string): string {
  const m: Record<string, string> = {
    'audio/webm': '.webm',
    'audio/webm;codecs=opus': '.webm',
    'audio/ogg': '.ogg',
    'audio/mp4': '.m4a',
    'audio/mpeg': '.mp3',
    'audio/wav': '.wav',
  }
  return m[mime.toLowerCase()] ?? '.bin'
}
