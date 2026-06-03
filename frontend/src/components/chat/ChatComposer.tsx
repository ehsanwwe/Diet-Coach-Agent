'use client'

import { useState } from 'react'
import type { Dictionary } from '@/dictionaries/fa'

interface Props {
  dict: Pick<Dictionary, 'companionChat'>
  onSend: (message: string) => Promise<void>
  disabled?: boolean
}

export default function ChatComposer({ dict, onSend, disabled }: Props) {
  const [text, setText] = useState('')
  const [sending, setSending] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const msg = text.trim()
    if (!msg || sending) return
    setSending(true)
    setText('')
    try {
      await onSend(msg)
    } finally {
      setSending(false)
    }
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e as unknown as React.FormEvent)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="flex items-end gap-3 p-4 bg-elevated border-t border-line">
      <textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={dict.companionChat.inputPlaceholder}
        rows={1}
        maxLength={4000}
        disabled={disabled || sending}
        className="flex-1 px-4 py-3 rounded-2xl bg-surface border border-line text-sm text-ink placeholder:text-ink-3 resize-none focus:outline-none focus:border-brand transition-colors disabled:opacity-50"
        style={{ maxHeight: 120, overflowY: 'auto' }}
      />
      <button
        type="submit"
        disabled={!text.trim() || sending || disabled}
        className="shrink-0 w-11 h-11 rounded-full bg-brand text-elevated flex items-center justify-center disabled:opacity-40 transition-opacity"
        aria-label={dict.companionChat.sendBtn}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
      </button>
    </form>
  )
}
