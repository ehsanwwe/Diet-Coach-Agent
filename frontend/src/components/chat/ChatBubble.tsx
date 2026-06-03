import type { ChatHistoryItem } from '@/types/chat'

interface Props {
  message: ChatHistoryItem
  youLabel: string
  coachLabel: string
}

export default function ChatBubble({ message, youLabel, coachLabel }: Props) {
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
        {message.content}
      </div>
    </div>
  )
}
