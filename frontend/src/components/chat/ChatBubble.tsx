'use client'

import { useEffect, useRef, useState } from 'react'
import { Copy, Pencil, RotateCcw, Send, X } from 'lucide-react'
import type { Dictionary } from '@/dictionaries/fa'
import type { ChatHistoryItem } from '@/types/chat'
import MarkdownMessage from './MarkdownMessage'

type ActionLabels = Pick<
  Dictionary['companionChat'],
  | 'copy'
  | 'copied'
  | 'edit'
  | 'sendBtn'
  | 'cancel'
  | 'editingMessage'
  | 'copyFailed'
  | 'retry'
>

interface Props {
  message: ChatHistoryItem
  coachLabel: string
  actions?: string[]
  failedLabel: string
  chips?: string[]
  actionLabels: ActionLabels
  isEditing?: boolean
  editText?: string
  editSubmitting?: boolean
  editError?: string | null
  canEdit?: boolean
  onChipPress?: (text: string) => void
  onEdit?: (message: ChatHistoryItem) => void
  onEditTextChange?: (text: string) => void
  onEditSend?: () => void
  onEditCancel?: () => void
}

function trimChip(text: string): string {
  return text.length > 32 ? `${text.slice(0, 30)}...` : text
}

async function writeClipboard(text: string): Promise<void> {
  if (navigator.clipboard?.writeText) {
    await navigator.clipboard.writeText(text)
    return
  }

  const textarea = document.createElement('textarea')
  textarea.value = text
  textarea.setAttribute('readonly', '')
  textarea.style.position = 'fixed'
  textarea.style.insetInlineStart = '-9999px'
  document.body.appendChild(textarea)
  textarea.select()
  const copied = document.execCommand('copy')
  textarea.remove()
  if (!copied) throw new Error('Clipboard copy failed')
}

export default function ChatBubble({
  message,
  coachLabel,
  actions,
  failedLabel,
  chips,
  actionLabels,
  isEditing = false,
  editText = '',
  editSubmitting = false,
  editError,
  canEdit = true,
  onChipPress,
  onEdit,
  onEditTextChange,
  onEditSend,
  onEditCancel,
}: Props) {
  const isUser = message.role === 'user'
  const isFailed = message.status === 'failed'
  const textareaRef = useRef<HTMLTextAreaElement>(null)
  const feedbackTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const [copyFeedback, setCopyFeedback] = useState<'copied' | 'failed' | null>(null)

  useEffect(() => {
    if (!isEditing || !textareaRef.current) return
    const textarea = textareaRef.current
    textarea.focus()
    textarea.setSelectionRange(textarea.value.length, textarea.value.length)
  }, [isEditing])

  useEffect(() => {
    if (!isEditing || !textareaRef.current) return
    const textarea = textareaRef.current
    textarea.style.height = 'auto'
    textarea.style.height = `${Math.min(Math.max(textarea.scrollHeight, 88), 320)}px`
  }, [editText, isEditing])

  useEffect(() => () => {
    if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current)
  }, [])

  async function handleCopy() {
    try {
      await writeClipboard(message.content)
      setCopyFeedback('copied')
    } catch {
      setCopyFeedback('failed')
    }
    if (feedbackTimerRef.current) clearTimeout(feedbackTimerRef.current)
    feedbackTimerRef.current = setTimeout(() => setCopyFeedback(null), 1800)
  }

  function handleEditorKeyDown(event: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === 'Escape') {
      event.preventDefault()
      onEditCancel?.()
      return
    }
    if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
      event.preventDefault()
      if (editText.trim() && !editSubmitting) onEditSend?.()
    }
  }

  return (
    <div className={`group flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
      {!isUser && (
        <span className="mb-0.5 px-1.5 text-[10px] text-ink-3">{coachLabel}</span>
      )}

      {isEditing && isUser ? (
        <div className="w-full max-w-[92%] rounded-2xl rounded-ee-sm bg-brand-muted p-3 shadow-sm">
          <label className="sr-only" htmlFor={`edit-${message.message_id}`}>
            {actionLabels.editingMessage}
          </label>
          <textarea
            ref={textareaRef}
            id={`edit-${message.message_id}`}
            value={editText}
            onChange={(event) => onEditTextChange?.(event.target.value)}
            onKeyDown={handleEditorKeyDown}
            disabled={editSubmitting}
            maxLength={4000}
            rows={3}
            className="block w-full resize-none overflow-y-auto rounded-xl border border-line bg-elevated px-3 py-2.5 text-start text-sm leading-relaxed text-ink outline-none transition-colors focus:border-brand disabled:opacity-60"
            aria-label={actionLabels.editingMessage}
          />
          {editError && <p className="mt-2 text-xs text-error" role="alert">{editError}</p>}
          <div className="mt-2 flex flex-wrap items-center justify-end gap-2">
            <button
              type="button"
              onClick={onEditCancel}
              disabled={editSubmitting}
              className="inline-flex min-h-9 items-center gap-1.5 rounded-lg px-3 text-xs font-semibold text-ink-2 transition-colors hover:bg-black/[0.05] disabled:opacity-50"
              aria-label={actionLabels.cancel}
            >
              <X aria-hidden="true" size={15} />
              {actionLabels.cancel}
            </button>
            <button
              type="button"
              onClick={onEditSend}
              disabled={!editText.trim() || editSubmitting}
              className="inline-flex min-h-9 items-center gap-1.5 rounded-lg bg-brand px-3 text-xs font-semibold text-elevated transition-opacity disabled:opacity-40"
              aria-label={editError ? actionLabels.retry : actionLabels.sendBtn}
            >
              {editError ? <RotateCcw aria-hidden="true" size={15} /> : <Send aria-hidden="true" size={15} />}
              {editError ? actionLabels.retry : actionLabels.sendBtn}
            </button>
          </div>
        </div>
      ) : (
        <div
          className={[
            'whitespace-pre-wrap break-words px-3.5 py-2.5 text-sm leading-relaxed',
            isUser
              ? 'max-w-[82%] rounded-2xl rounded-ee-sm bg-brand text-elevated'
              : 'max-w-[90%] rounded-2xl rounded-es-sm border border-black/[0.06] bg-elevated text-ink shadow-sm',
          ].join(' ')}
        >
          {isUser ? (
            message.content
          ) : isFailed ? (
            <span className="text-xs text-error">{failedLabel}</span>
          ) : (
            <MarkdownMessage content={message.content} />
          )}
        </div>
      )}

      {!isEditing && (
        <div className={`mt-1 flex min-h-9 items-center gap-0.5 px-0.5 ${isUser ? 'self-end' : 'self-start'}`}>
          <button
            type="button"
            onClick={handleCopy}
            className="inline-flex min-h-9 items-center gap-1 rounded-lg px-2 text-[11px] text-ink-3 transition-colors hover:bg-black/[0.05] hover:text-ink focus-visible:outline-2 focus-visible:outline-brand"
            aria-label={actionLabels.copy}
          >
            <Copy aria-hidden="true" size={14} />
            <span>{actionLabels.copy}</span>
          </button>
          {isUser && (
            <button
              type="button"
              onClick={() => onEdit?.(message)}
              disabled={!canEdit}
              className="inline-flex min-h-9 items-center gap-1 rounded-lg px-2 text-[11px] text-ink-3 transition-colors hover:bg-black/[0.05] hover:text-ink disabled:cursor-not-allowed disabled:opacity-40 focus-visible:outline-2 focus-visible:outline-brand"
              aria-label={actionLabels.edit}
            >
              <Pencil aria-hidden="true" size={14} />
              <span>{actionLabels.edit}</span>
            </button>
          )}
          {copyFeedback && (
            <span className={`px-1 text-[11px] ${copyFeedback === 'failed' ? 'text-error' : 'text-ink-3'}`} role="status">
              {copyFeedback === 'copied' ? actionLabels.copied : actionLabels.copyFailed}
            </span>
          )}
        </div>
      )}

      {!isUser && !isFailed && actions && actions.length > 0 && (
        <div className="mt-1.5 flex flex-wrap gap-1 px-0.5">
          {actions.map((action) => (
            <span key={action} className="rounded-full bg-brand-muted px-2 py-0.5 text-[10px] leading-snug text-ink-3">
              {trimChip(action)}
            </span>
          ))}
        </div>
      )}

      {!isUser && !isFailed && chips && chips.length > 0 && (
        <div className="mt-2 flex flex-wrap gap-1.5 px-0.5">
          {chips.map((chip) => (
            <button
              key={chip}
              type="button"
              onClick={() => onChipPress?.(chip)}
              className="rounded-full border border-brand/25 bg-elevated px-3 py-1.5 text-xs leading-snug text-brand-dark transition-opacity active:opacity-60"
            >
              {chip}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
