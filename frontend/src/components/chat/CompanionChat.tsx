'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import type { Dictionary } from '@/dictionaries/fa'
import type { Locale } from '@/lib/i18n'
import type { ChatHistoryItem } from '@/types/chat'
import { getChatHistory, sendChatMessage, clearChatMemory } from '@/lib/chat'
import { getStoredUser } from '@/lib/storage'
import ChatBubble from './ChatBubble'
import ChatComposer from './ChatComposer'
import AppIcon from '@/components/ui/AppIcon'

interface Props {
  dict: Pick<Dictionary, 'companionChat' | 'common'>
  locale: Locale
}

const DRAFT_KEY_PREFIX = 'chat_draft_'
const POLL_INTERVAL_MS = 2000
const SUBMITTED_DRAFT_MAX_AGE_MS = 90_000

interface StoredDraft {
  text: string
  clientMessageId: string
  status: 'draft' | 'submitted'
  submittedAt?: string
}

function makeClientId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2)}`
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
  const [pendingRecovery, setPendingRecovery] = useState(false)
  const [started, setStarted] = useState(false)
  const [showClearConfirm, setShowClearConfirm] = useState(false)
  const [clearing, setClearing] = useState(false)
  const [draftText, setDraftText] = useState('')

  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const mountedRef = useRef(true)
  const userIdRef = useRef<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // ── Draft helpers ──────────────────────────────────────────────────────────

  const clientMessageIdRef = useRef<string>(makeClientId())

  function getDraftKey(): string | null {
    return userIdRef.current ? `${DRAFT_KEY_PREFIX}${userIdRef.current}` : null
  }

  function saveDraftToStorage(text: string) {
    if (typeof window === 'undefined') return
    const key = getDraftKey()
    if (!key) return
    if (!text) {
      localStorage.removeItem(key)
      return
    }
    const entry: StoredDraft = {
      text,
      clientMessageId: clientMessageIdRef.current,
      status: 'draft',
    }
    localStorage.setItem(key, JSON.stringify(entry))
  }

  function markDraftSubmitted(text: string) {
    if (typeof window === 'undefined') return
    const key = getDraftKey()
    if (!key) return
    const entry: StoredDraft = {
      text,
      clientMessageId: clientMessageIdRef.current,
      status: 'submitted',
      submittedAt: new Date().toISOString(),
    }
    localStorage.setItem(key, JSON.stringify(entry))
  }

  function clearDraftFromStorage() {
    if (typeof window === 'undefined') return
    const key = getDraftKey()
    if (key) localStorage.removeItem(key)
  }

  function handleDraftChange(text: string) {
    setDraftText(text)
    saveDraftToStorage(text)
  }

  // ── Polling helpers ────────────────────────────────────────────────────────

  function stopPolling() {
    if (pollingRef.current !== null) {
      clearInterval(pollingRef.current)
      pollingRef.current = null
    }
  }

  function startPolling() {
    stopPolling()
    pollingRef.current = setInterval(async () => {
      if (!mountedRef.current) {
        stopPolling()
        return
      }
      try {
        const data = await getChatHistory()
        if (!mountedRef.current) {
          stopPolling()
          return
        }
        const hasPending = data.messages.some(
          (m) => m.role === 'assistant' && m.status === 'pending'
        )
        setMessages(data.messages.filter((m) => m.status !== 'pending'))
        if (!hasPending) {
          stopPolling()
          setPendingRecovery(false)
        }
      } catch {
        // Ignore transient polling errors — next tick retries automatically
      }
    }, POLL_INTERVAL_MS)
  }

  // ── Mount / unmount ────────────────────────────────────────────────────────

  useEffect(() => {
    mountedRef.current = true

    // Resolve user identity and restore draft (client-only)
    const user = getStoredUser<{ id: string }>()
    userIdRef.current = user?.id ?? null
    if (user?.id && typeof window !== 'undefined') {
      const raw = localStorage.getItem(`${DRAFT_KEY_PREFIX}${user.id}`) ?? ''
      if (raw) {
        try {
          const stored: StoredDraft = JSON.parse(raw)
          if (stored.status === 'submitted') {
            // Already sent — check if stale and clean up
            const age = stored.submittedAt
              ? Date.now() - new Date(stored.submittedAt).getTime()
              : SUBMITTED_DRAFT_MAX_AGE_MS + 1
            if (age > SUBMITTED_DRAFT_MAX_AGE_MS) {
              localStorage.removeItem(`${DRAFT_KEY_PREFIX}${user.id}`)
            }
            // Do NOT populate composer with a submitted message
          } else {
            // status === 'draft' — restore text to composer
            setDraftText(stored.text ?? '')
            if (stored.clientMessageId) {
              clientMessageIdRef.current = stored.clientMessageId
            }
          }
        } catch {
          // Legacy plain-string draft — restore as-is
          setDraftText(raw)
        }
      }
    }

    getChatHistory()
      .then((data) => {
        if (!mountedRef.current) return
        const hasPending = data.messages.some(
          (m) => m.role === 'assistant' && m.status === 'pending'
        )
        const visible = data.messages.filter((m) => m.status !== 'pending')
        setMessages(visible)
        if (visible.length > 0) setStarted(true)
        if (hasPending) {
          setPendingRecovery(true)
          startPolling()
        }
      })
      .catch((err) => {
        if (!mountedRef.current) return
        if (err instanceof Error && err.message === 'UNAUTHORIZED') {
          const loginPath = `/${locale}/login`
          if (pathname !== loginPath) routerRef.current.replace(loginPath)
          return
        }
        setLoadError(dict.companionChat.loadError)
      })
      .finally(() => {
        if (mountedRef.current) setLoading(false)
      })

    return () => {
      mountedRef.current = false
      stopPolling()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [locale])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, typing, pendingRecovery])

  // ── Send ───────────────────────────────────────────────────────────────────

  async function handleSend(message: string) {
    setSendError(null)
    setDraftText('')            // Clear input UI immediately

    // Capture the current client ID for this send, then rotate for the next message.
    const clientMessageId = clientMessageIdRef.current
    clientMessageIdRef.current = makeClientId()

    // Mark as submitted in localStorage BEFORE the network call so that if the
    // component unmounts mid-request (user navigates away) the message is never
    // restored to the composer on return.
    markDraftSubmitted(message)
    const optimistic: ChatHistoryItem = {
      message_id: `tmp-${clientMessageId}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
      status: 'completed',
    }
    setMessages((prev) => [...prev, optimistic])
    setTyping(true)
    setStarted(true)

    try {
      const resp = await sendChatMessage(message, clientMessageId)
      // Clear draft from localStorage regardless of mount state — localStorage is
      // a global store and does not need the component to be mounted.
      clearDraftFromStorage()

      if (!mountedRef.current) return

      const assistant: ChatHistoryItem = {
        message_id: resp.message_id,
        role: resp.role,
        content: resp.content,
        created_at: resp.created_at,
        status: 'completed',
      }
      setMessages((prev) => [
        ...prev.filter((m) => m.message_id !== optimistic.message_id),
        { ...optimistic },
        assistant,
      ])
      if (resp.actions_summary?.length) {
        setMessageExtras((prev) => ({
          ...prev,
          [resp.message_id]: { actions: resp.actions_summary! },
        }))
      }
    } catch (err) {
      // On error, restore the draft so the user can retry.
      saveDraftToStorage(message)
      if (!mountedRef.current) return
      if (err instanceof Error && err.message === 'UNAUTHORIZED') {
        const loginPath = `/${locale}/login`
        if (pathname !== loginPath) routerRef.current.replace(loginPath)
        return
      }
      setSendError(dict.companionChat.sendError)
      setMessages((prev) => prev.filter((m) => m.message_id !== optimistic.message_id))
    } finally {
      if (mountedRef.current) setTyping(false)
    }
  }

  // ── Clear ──────────────────────────────────────────────────────────────────

  async function handleClear() {
    setClearing(true)
    try {
      await clearChatMemory()
      setMessages([])
      setStarted(false)
      setShowClearConfirm(false)
      stopPolling()
      setPendingRecovery(false)
    } catch {
      setShowClearConfirm(false)
    } finally {
      setClearing(false)
    }
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  const showThinking = typing || pendingRecovery

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
            <AppIcon name="chat" className="text-brand" size={34} />
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
            failedLabel={dict.companionChat.assistantFailed}
          />
        ))}
        {showThinking && (
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

      <ChatComposer
        dict={dict}
        onSend={handleSend}
        value={draftText}
        onChange={handleDraftChange}
      />
    </div>
  )
}
