import type { ChatHistoryItem } from '@/types/chat'
import MarkdownMessage from './MarkdownMessage'

interface Props {
  message: ChatHistoryItem
  youLabel: string
  coachLabel: string
  actions?: string[]
}

export default function ChatBubble({ message, youLabel, coachLabel, actions }: Props) {
  const isUser = message.role === 'user'
  return (
    <div className={`flex flex-col gap-1 ${isUser ? 'items-end' : 'items-start'}`}>
      <span className="text-xs text-ink-3 px-1">
        {isUser ? youLabel : coachLabel}
      </span>
      <div
        className={[
          'max-w-[80%] px-4 py-3 rounded-2xl text-sm leading-relaxed',
          isUser
            ? 'bg-brand text-elevated rounded-ee-sm'
            : 'bg-elevated text-ink rounded-es-sm shadow-sm',
        ].join(' ')}
      >
        {isUser ? (
          message.content
        ) : (
          <MarkdownMessage content={message.content} />
        )}
      </div>
      {!isUser && actions && actions.length > 0 && (
        <div className="flex flex-wrap gap-1.5 mt-2 max-w-[80%]">
          {actions.map((a, i) => (
            <span key={i} className="text-xs bg-brand-muted text-ink-2 px-2.5 py-1 rounded-full">
              {a}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
