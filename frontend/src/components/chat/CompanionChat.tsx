'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import type { ChatHistoryItem } from '@/types/chat'
import { getChatHistory, sendChatMessage } from '@/lib/chat'
import ChatBubble from './ChatBubble'
import ChatComposer from './ChatComposer'

interface Props {
  dict: Pick<Dictionary, 'companionChat' | 'common'>
  locale: Locale
}

export default function CompanionChat({ dict, locale }: Props) {
  const router = useRouter()
  const routerRef = useRef(router)
  routerRef.current = router
  const pathname = usePathname()
  const [messages, setMessages] = useState<ChatHistoryItem[]>([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [sendError, setSendError] = useState<string | null>(null)
  const [typing, setTyping] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getChatHistory()
      .then((data) => setMessages(data.messages))
      .catch((err) => {
        if (err?.message === 'UNAUTHORIZED') {
          const loginPath = `/${locale}/login`
          if (pathname !== loginPath) routerRef.current.replace(loginPath)
          return
        }
        setLoadError(dict.companionChat.loadError)
      })
      .finally(() => setLoading(false))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing])

  async function handleSend(message: string) {
    setSendError(null)
    const optimistic: ChatHistoryItem = {
      message_id: `tmp-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, optimistic])
    setTyping(true)
    try {
      const resp = await sendChatMessage(message)
      const assistant: ChatHistoryItem = {
        message_id: resp.message_id,
        role: resp.role,
        content: resp.content,
        created_at: resp.created_at,
      }
      setMessages((prev) => [...prev, assistant])
    } catch (err) {
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        const loginPath = `/${locale}/login`
        if (pathname !== loginPath) routerRef.current.replace(loginPath)
        return
      }
      setSendError(dict.companionChat.sendError)
      setMessages((prev) => prev.filter((m) => m.message_id !== optimistic.message_id))
    } finally {
      setTyping(false)
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin" />
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="flex-1 flex items-center justify-center p-8 text-center">
        <p className="text-sm text-error">{loadError}</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col flex-1 min-h-0">
      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center py-16 text-center gap-3">
            <div className="w-16 h-16 rounded-full bg-brand-muted flex items-center justify-center text-2xl">🤝</div>
            <p className="text-base font-semibold text-ink">{dict.companionChat.emptyTitle}</p>
            <p className="text-sm text-ink-2 max-w-[260px]">{dict.companionChat.emptyDesc}</p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatBubble
            key={msg.message_id}
            message={msg}
            youLabel={dict.companionChat.you}
            coachLabel={dict.companionChat.coach}
          />
        ))}
        {typing && (
          <div className="flex items-start gap-2">
            <div className="px-4 py-3 rounded-2xl rounded-es-sm bg-elevated shadow-sm">
              <span className="text-xs text-ink-3">{dict.companionChat.typingIndicator}</span>
            </div>
          </div>
        )}
        {sendError && (
          <p className="text-xs text-error text-center">{sendError}</p>
        )}
        <div ref={bottomRef} />
      </div>
      <ChatComposer dict={dict} onSend={handleSend} />
    </div>
  )
}
