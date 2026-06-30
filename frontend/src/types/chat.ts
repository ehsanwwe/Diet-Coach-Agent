export interface ChatMessageResponse {
  message_id: string
  role: string
  content: string
  provider: string
  is_mock: boolean
  created_at: string
  actions_summary?: string[] | null
  tool_calls_executed?: number | null
  suggestion_chips?: string[] | null
}

export interface ChatHistoryItem {
  message_id: string
  role: string
  content: string
  created_at: string
  status?: string
  error_message?: string | null
}

export interface ChatHistoryResponse {
  session_id: string | null
  messages: ChatHistoryItem[]
}
