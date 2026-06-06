'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import type { ChatHistoryItem } from '@/types/chat'
import { getChatHistory, sendChatMessage, clearChatMemory } from '@/lib/chat'
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
  const [messageExtras, setMessageExtras] = useState<Record<string, { actions?: string[] }>>({})
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [sendError, setSendError] = useState<string | null>(null)
  const [typing, setTyping] = useState(false)
  const [started, setStarted] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [clearing, setClearing] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    getChatHistory()
      .then((data) => {
        setMessages(data.messages)
        if (data.messages.length > 0) setStarted(true)
      })
      .catch((err) => {
        if (err instanceof Error && err.message === 'UNAUTHORIZED') {
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
      if (resp.actions_summary?.length) {
        setMessageExtras(prev => ({ ...prev, [resp.message_id]: { actions: resp.actions_summary! } }))
      }
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

  async function handleClear() {
    setClearing(true)
    try {
      await clearChatMemory()
      setMessages([])
      setStarted(false)
      setShowClearConfirm(false)
    } catch {
      setShowClearConfirm(false)
    } finally {
      setClearing(false)
    }
  }

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center min-h-[60vh]">
        <div
          role="status"
          aria-label={dict.common.loading}
          className="w-8 h-8 rounded-full border-2 border-brand border-t-transparent animate-spin"
        />
      </div>
    )
  }

  if (loadError) {
    return (
      <div className="flex-1 px-5 pt-6 pb-28">
        <div className="rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-3">
          <p className="text-sm text-error">{loadError}</p>
        </div>
      </div>
    )
  }

  // Empty state — user hasn't started a conversation yet
  if (messages.length === 0 && !started) {
    return (
      <div className="flex-1 overflow-y-auto px-5 pt-6 pb-28">
        <div className="rounded-2xl bg-elevated p-6 shadow-sm text-center space-y-4">
          <div className="mx-auto w-20 h-20 rounded-full bg-brand-muted flex items-center justify-center">
            <span className="text-3xl">💬</span>
          </div>
          <h2 className="text-xl font-bold text-ink">{dict.companionChat.emptyTitle}</h2>
          <p className="text-sm text-ink-2 leading-relaxed">{dict.companionChat.emptyDesc}</p>
          <button
            type="button"
            onClick={() => setStarted(true)}
            className="mt-2 w-full py-3 px-5 rounded-2xl bg-brand text-elevated text-sm font-bold transition-opacity active:opacity-80"
          >
            {dict.companionChat.startChat}
          </button>
        </div>
      </div>
    )
  }

  // Active chat — started or has messages
  return (
    <div className="flex flex-col flex-1 min-h-0">
      {/* Clear memory row — only visible when there are messages */}
      {messages.length > 0 && (
        <div className="px-4 pt-2 pb-1 flex justify-end items-center gap-2 shrink-0">
          {showClearConfirm ? (
            <>
              <span className="text-xs text-ink-3">{dict.companionChat.clearMemoryConfirmTitle}</span>
              <button
                type="button"
                onClick={handleClear}
                disabled={clearing}
                className="text-xs text-error font-semibold disabled:opacity-50"
              >
                {clearing ? '...' : dict.companionChat.clearMemoryConfirm}
              </button>
              <button
                type="button"
                onClick={() => setShowClearConfirm(false)}
                className="text-xs text-ink-3"
              >
                {dict.companionChat.clearMemoryCancel}
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => setShowClearConfirm(true)}
              className="text-xs text-ink-3 hover:text-error transition-colors py-1"
            >
              {dict.companionChat.clearMemory}
            </button>
          )}
        </div>
      )}

      {/* Message list */}
      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
        {messages.length === 0 && started && (
          <div className="text-center py-6">
            <p className="text-sm text-ink-3">{dict.companionChat.emptyDesc}</p>
          </div>
        )}
        {messages.map((msg) => (
          <ChatBubble
            key={msg.message_id}
            message={msg}
            youLabel={dict.companionChat.you}
            coachLabel={dict.companionChat.coach}
            actions={messageExtras[msg.message_id]?.actions}
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
