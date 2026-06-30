import type { ChatHistoryItem } from '@/types/chat'
import MarkdownMessage from './MarkdownMessage'

interface Props {
  message: ChatHistoryItem
  youLabel: string
  coachLabel: string
  actions?: string[]
  failedLabel: string
  chips?: string[]
  onChipPress?: (text: string) => void
}

function trimChip(text: string): string {
  return text.length > 32 ? text.slice(0, 30) + '…' : text
}

export default function ChatBubble({ message, coachLabel, actions, failedLabel, chips, onChipPress }: Props) {
  const isUser = message.role === 'user'
  const isFailed = message.status === 'failed'

  return (
    <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
      {/* Coach label — assistant only, very subtle */}
      {!isUser && (
        <span className="text-[10px] text-ink-3 px-1.5 mb-0.5">{coachLabel}</span>
      )}

      <div
        className={[
          'px-3.5 py-2.5 text-sm leading-relaxed break-words',
          isUser
            ? 'max-w-[82%] bg-brand text-elevated rounded-2xl rounded-ee-sm'
            : 'max-w-[90%] bg-elevated text-ink rounded-2xl rounded-es-sm shadow-sm border border-black/[0.06]',
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

      {/* Action chips — read-only informational labels */}
      {!isUser && !isFailed && actions && actions.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-1.5 px-0.5">
          {actions.map((a, i) => (
            <span
              key={i}
              className="text-[10px] bg-brand-muted text-ink-3 px-2 py-0.5 rounded-full leading-snug"
            >
              {trimChip(a)}
            </span>
          ))}
        </div>
      )}

      {/* Suggestion chips — tappable quick-reply buttons */}
      {!isUser && !isFailed && chips && chips.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2 px-0.5">
          {chips.map((chip, i) => (
            <button
              key={i}
              type="button"
              onClick={() => onChipPress?.(chip)}
              className="text-xs bg-elevated border border-brand/25 text-brand-dark px-3 py-1.5 rounded-full leading-snug active:opacity-60 transition-opacity"
            >
              {chip}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
