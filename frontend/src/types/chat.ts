export interface ChatMessageResponse {
  message_id: string
  role: string
  content: string
  provider: string
  is_mock: boolean
  created_at: string
}

export interface ChatHistoryItem {
  message_id: string
  role: string
  content: string
  created_at: string
}

export interface ChatHistoryResponse {
  session_id: string | null
  messages: ChatHistoryItem[]
}
