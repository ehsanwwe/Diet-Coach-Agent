'use client'

import { useEffect, useRef, useState } from 'react'
import { Send } from 'lucide-react'
import { cn } from '@/lib/cn'
import { sendTextMessage, uploadAudio, getChatHistory } from '@/lib/onboardingChat'
import type { ChatHistoryItem } from '@/types/onboardingChat'
import AudioRecorder from '@/components/audio/AudioRecorder'
import AppIcon from '@/components/ui/AppIcon'

interface AudioDict {
  startRecording: string
  stopRecording: string
  cancelRecording: string
  sendAudio: string
  recording: string
  uploading: string
  permissionDenied: string
  unsupportedBrowser: string
  noMicrophone: string
  audioPreview: string
  recordingDuration: string
  uploadFailed: string
  uploadSuccess: string
  labelPlay: string
  labelPause: string
  labelReset: string
  textPlaceholder: string
  sendText: string
  historyEmpty: string
  transcriptionPending: string
  transcriptionNotConfigured: string
  processing: string
}

interface Props {
  dict: AudioDict
  enabled: boolean
}

export default function OnboardingHabitChat({ dict, enabled }: Props) {
  const [items, setItems] = useState<ChatHistoryItem[]>([])
  const [text, setText] = useState('')
  const [isSendingText, setIsSendingText] = useState(false)
  const [isUploadingAudio, setIsUploadingAudio] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [textError, setTextError] = useState<string | null>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!enabled) return
    getChatHistory()
      .then((res) => setItems(res.data.items))
      .catch(() => {})
  }, [enabled])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [items])

  const handleSendText = async () => {
    const trimmed = text.trim()
    if (!trimmed) return
    setIsSendingText(true)
    setTextError(null)
    try {
      const res = await sendTextMessage(trimmed)
      setText('')
      const newItems: ChatHistoryItem[] = [
        {
          kind: 'text',
          id: res.data.user_message.id,
          session_id: res.data.user_message.session_id,
          role: res.data.user_message.role,
          content: res.data.user_message.content,
          created_at: res.data.user_message.created_at,
        },
      ]
      if (res.data.assistant_message) {
        newItems.push({
          kind: 'text',
          id: res.data.assistant_message.id,
          session_id: res.data.assistant_message.session_id,
          role: res.data.assistant_message.role,
          content: res.data.assistant_message.content,
          created_at: res.data.assistant_message.created_at,
        })
      }
      setItems((prev) => [...prev, ...newItems])
    } catch (err) {
      setTextError(err instanceof Error ? err.message : dict.uploadFailed)
    } finally {
      setIsSendingText(false)
    }
  }

  const handleSendAudio = async (blob: Blob, mimeType: string, duration: number) => {
    setIsUploadingAudio(true)
    setUploadError(null)
    try {
      const res = await uploadAudio(blob, mimeType, duration)
      const audioItem: ChatHistoryItem = {
        kind: 'audio',
        id: res.data.id,
        session_id: res.data.session_id,
        storage_key: res.data.storage_key,
        mime_type: res.data.mime_type,
        size_bytes: res.data.size_bytes,
        duration_seconds: res.data.duration_seconds,
        transcription_status: res.data.transcription_status,
        created_at: res.data.created_at,
      }
      setItems((prev) => [...prev, audioItem])
    } catch (err) {
      setUploadError(err instanceof Error ? err.message : dict.uploadFailed)
      throw err
    } finally {
      setIsUploadingAudio(false)
    }
  }

  return (
    <div className="flex flex-col gap-3">
      {/* History */}
      <div className="flex flex-col gap-2 max-h-56 overflow-y-auto px-1">
        {items.length === 0 && enabled && (
          <p className="text-xs text-ink-3 text-center py-4">{dict.historyEmpty}</p>
        )}
        {items.map((item) => (
          <ChatBubble key={item.id} item={item} dict={dict} />
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input area */}
      <div className={cn('space-y-2', !enabled && 'opacity-40 pointer-events-none select-none')}>
        {/* Text input */}
        <div className="flex gap-2">
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                handleSendText()
              }
            }}
            placeholder={dict.textPlaceholder}
            rows={2}
            disabled={!enabled || isSendingText}
            className={cn(
              'flex-1 rounded-2xl px-4 py-3 text-sm bg-surface border border-line',
              'placeholder:text-ink-3 text-ink resize-none',
              'focus:outline-none focus:border-brand transition-colors',
              !enabled && 'cursor-not-allowed',
            )}
          />
          <button
            type="button"
            onClick={handleSendText}
            disabled={!enabled || !text.trim() || isSendingText}
            className={cn(
              'self-end flex-shrink-0 w-10 h-10 rounded-2xl flex items-center justify-center transition-colors',
              enabled && text.trim() && !isSendingText
                ? 'bg-brand text-white hover:bg-brand/90'
                : 'bg-line text-ink-3 cursor-not-allowed',
            )}
          >
            <Send size={16} />
          </button>
        </div>
        {textError && <p className="text-xs text-error px-1">{textError}</p>}

        {/* Audio recorder */}
        <AudioRecorder
          dict={dict}
          onSend={handleSendAudio}
          isUploading={isUploadingAudio}
          uploadError={uploadError}
          disabled={!enabled}
        />
      </div>
    </div>
  )
}

function ChatBubble({ item, dict }: { item: ChatHistoryItem; dict: AudioDict }) {
  if (item.kind === 'text') {
    const isUser = item.role === 'user'
    return (
      <div className={cn('flex', isUser ? 'justify-end' : 'justify-start')}>
        <div
          className={cn(
            'max-w-[80%] rounded-2xl px-3 py-2 text-sm',
            isUser
              ? 'bg-brand text-white rounded-br-sm'
              : 'bg-surface border border-line text-ink rounded-bl-sm',
          )}
        >
          {item.content}
        </div>
      </div>
    )
  }

  // Audio item
  const statusLabel =
    item.transcription_status === 'not_configured'
      ? dict.transcriptionNotConfigured
      : item.transcription_status === 'pending'
        ? dict.transcriptionPending
        : dict.processing

  return (
    <div className="flex justify-end">
      <div className="max-w-[80%] rounded-2xl rounded-br-sm bg-brand/10 border border-brand/20 px-3 py-2 text-sm text-ink">
        <div className="flex items-center gap-1.5">
          <AppIcon name="microphone" className="text-brand" size={16} />
          {item.duration_seconds != null && (
            <span className="text-xs text-ink-2">
              {Math.round(item.duration_seconds)}s
            </span>
          )}
        </div>
        <p className="text-xs text-ink-3 mt-0.5">{statusLabel}</p>
      </div>
    </div>
  )
}
