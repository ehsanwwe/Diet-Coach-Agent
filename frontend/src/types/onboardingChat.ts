export interface ChatMessageOut {
  id: string
  session_id: string
  role: string
  content: string
  created_at: string
}

export interface TextMessageResponse {
  session_id: string
  user_message: ChatMessageOut
  assistant_message: ChatMessageOut | null
}

export interface AudioUploadResponse {
  id: string
  session_id: string
  storage_key: string
  mime_type: string | null
  size_bytes: number | null
  duration_seconds: number | null
  transcription_status: string
  created_at: string
}

export interface ChatHistoryItem {
  kind: 'text' | 'audio'
  id: string
  session_id: string
  // text
  role?: string | null
  content?: string | null
  // audio
  storage_key?: string | null
  mime_type?: string | null
  size_bytes?: number | null
  duration_seconds?: number | null
  transcription_status?: string | null
  created_at: string
}

export interface ChatHistoryResponse {
  session_id: string | null
  items: ChatHistoryItem[]
  total: number
}
